from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..auth import (clear_session_cookie, create_token, get_current_user, hash_password, set_session_cookie,
                    verify_password)
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, ProfileOut, ProfileUpdate, RegisterIn, TokenOut
from ..security import (anon, client_ip, log, login_fail_limiter, login_ip_limiter, raise_if_blocked,
                        register_limiter)

router = APIRouter(prefix="/api", tags=["Auth & profile"])


def profile_out(user: User) -> ProfileOut:
    return ProfileOut(
        id=user.id, name=user.name, email=user.email,
        goals=[g for g in (user.goals or "").split(",") if g],
        activity_level=user.activity_level,
        has_restrictions=bool(user.has_restrictions),
        ai_consent=bool(user.ai_consent),
    )


@router.post("/auth/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = client_ip(request)
    raise_if_blocked(register_limiter, ip, "Too many sign-ups from this network. Please try again later.")
    register_limiter.hit(ip)
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id)
    set_session_cookie(response, token)
    return TokenOut(access_token=token, user=profile_out(user))


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = client_ip(request)
    raise_if_blocked(login_ip_limiter, ip, "Too many login attempts. Please wait a few minutes.")
    login_ip_limiter.hit(ip)
    raise_if_blocked(login_fail_limiter, data.email, "Too many failed attempts for this account. Try again later.")
    user = db.query(User).filter(User.email == data.email).first()
    if user is None or not verify_password(data.password, user.password_hash):
        login_fail_limiter.hit(data.email)
        log.warning("login failed ip=%s account=%s", ip, anon(data.email))
        # Same message in both cases so attackers cannot learn which emails exist
        raise HTTPException(401, "Incorrect email or password")
    login_fail_limiter.reset(data.email)
    token = create_token(user.id)
    set_session_cookie(response, token)
    return TokenOut(access_token=token, user=profile_out(user))


@router.post("/auth/logout", status_code=204)
def logout():
    resp = Response(status_code=204)
    clear_session_cookie(resp)
    return resp


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return profile_out(user)


@router.put("/profile", response_model=ProfileOut)
def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.name is not None:
        user.name = data.name.strip()
    if data.goals is not None:
        user.goals = ",".join(dict.fromkeys(data.goals))
    if data.activity_level is not None:
        user.activity_level = data.activity_level
    if data.has_restrictions is not None:
        user.has_restrictions = data.has_restrictions
    if data.ai_consent is not None:
        user.ai_consent = data.ai_consent
    db.commit()
    db.refresh(user)
    return profile_out(user)
