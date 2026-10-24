"""MediMate AI - FastAPI entry point.  Run:  uvicorn app.main:app --reload"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import config, models  # noqa: F401  (models must be imported so tables are registered)
from .database import Base, engine
from .routers import account, appointments, auth, chatbot, health_records, recommendations

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("medimate")

# Refuse to start with an unsafe production configuration.
if config.IS_PROD:
    problems = []
    if len(config.SECRET_KEY) < 32:
        problems.append("SECRET_KEY must be a random value of at least 32 characters")
    if "*" in config.CORS_ORIGINS:
        problems.append("CORS_ORIGINS must not contain '*'")
    if not config.COOKIE_SECURE:
        problems.append("COOKIE_SECURE must be true in production (serve the site over HTTPS)")
    if config.DATABASE_URL.startswith("sqlite") and not config.ALLOW_SQLITE_IN_PROD:
        problems.append("DATABASE_URL must be a persistent Postgres database (SQLite files are lost when free hosts restart)")
    if problems:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(problems))

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MediMate AI API",
    description="Personal wellness tracker. Not a medical device; does not diagnose or prescribe.",
    version="2.0.0",
    # API docs are for development only
    docs_url=None if config.IS_PROD else "/docs",
    redoc_url=None,
    openapi_url=None if config.IS_PROD else "/openapi.json",
)
if config.ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api"):
        resp.headers["Cache-Control"] = "no-store"  # health data must not be cached
    if config.IS_PROD:
        if request.url.path.startswith("/api"):
            resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        else:  # the React site: only our own scripts, no framing, no outside connections
            resp.headers["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


# Every error uses the same JSON shape: {"error": {"status": 422, "message": "...", "details": [...]}}
@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, headers=getattr(exc, "headers", None),
                        content={"error": {"status": exc.status_code, "message": str(exc.detail), "details": []}})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    details = []
    for e in exc.errors():
        field = ".".join(str(p) for p in e["loc"] if p != "body")
        details.append({"field": field, "message": str(e["msg"]).replace("Value error, ", "")})
    message = details[0]["message"] if details else "Invalid input"
    return JSONResponse(status_code=422, content={"error": {"status": 422, "message": message, "details": details}})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)  # details stay in the server log
    return JSONResponse(status_code=500, content={"error": {"status": 500, "message": "Something went wrong on our side.", "details": []}})


for r in (auth.router, account.router, health_records.router, appointments.router, chatbot.router,
          recommendations.router):
    app.include_router(r)


if not config.IS_PROD:
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/docs")


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/api/config", tags=["System"])
def public_config():
    """Non-secret settings the web page needs (shown in the privacy notice)."""
    return {"contact_email": config.CONTACT_EMAIL}


# Production: serve the built React site from this same server (one address => simple, safe cookies).
# Mounted LAST so every /api route above wins.
if config.STATIC_DIR and os.path.isdir(config.STATIC_DIR):
    app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="frontend")
