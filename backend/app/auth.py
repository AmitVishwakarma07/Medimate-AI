"""Password hashing (bcrypt), login tokens (JWT) and session cookies.

Browser sessions use an httpOnly cookie (JavaScript cannot read it, which limits damage from XSS).
Because cookies are sent automatically by browsers, state-changing requests that rely on the cookie
must also carry the header  X-Requested-With: MediMate  (CSRF defence, together with SameSite=Lax).
API clients may instead send  Authorization: Bearer <token>  (not affected by CSRF).
Limits: no email verification, no refresh/revocation (tokens simply expire)."""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import User

SECRET_KEY = config.SECRET_KEY or secrets.token_urlsafe(32)  # random if unset (main.py refuses this in production)
ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)
CSRF_VALUE = "MediMate"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def set_session_cookie(response: Response, token: str):
    response.set_cookie(config.COOKIE_NAME, token, max_age=config.TOKEN_MINUTES * 60, httponly=True,
                        secure=config.COOKIE_SECURE, samesite="lax", path="/")


def clear_session_cookie(response: Response):
    response.delete_cookie(config.COOKIE_NAME, path="/", secure=config.COOKIE_SECURE, httponly=True, samesite="lax")


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=401, detail="Not authenticated. Please log in.",
                                 headers={"WWW-Authenticate": "Bearer"})
    if creds is not None:
        token = creds.credentials
    else:
        token = request.cookies.get(config.COOKIE_NAME)
        if token and request.method not in SAFE_METHODS and request.headers.get("x-requested-with") != CSRF_VALUE:
            raise HTTPException(403, "Missing security header")
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    if user is None:
        raise unauthorized
    return user
