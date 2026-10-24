"""Reads settings from environment variables (and an optional .env file)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv is optional
    pass

def normalize_database_url(url: str) -> str:
    """Some hosts hand out 'postgres://...'; SQLAlchemy needs 'postgresql://...'."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./medimate.db"))
SECRET_KEY = os.getenv("SECRET_KEY", "")
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "120"))
DEMO_MODE = os.getenv("DEMO_MODE", "false" if os.getenv("ENV", "development").lower() == "production" else "true").lower() == "true"
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
# Optional external AI. Empty key => rule-based fallback only.
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "")

# ---------- production / security settings ----------
ENV = os.getenv("ENV", "development").lower()          # set ENV=production when deployed
IS_PROD = ENV == "production"
COOKIE_NAME = "mm_session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if IS_PROD else "false").lower() == "true"
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"   # true only behind your own reverse proxy
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
LOGIN_MAX_PER_IP = int(os.getenv("LOGIN_MAX_PER_IP", "30"))          # per 5 minutes
LOGIN_MAX_FAILS = int(os.getenv("LOGIN_MAX_FAILS", "5"))             # per account, per 15 minutes
REGISTER_MAX_PER_HOUR = int(os.getenv("REGISTER_MAX_PER_HOUR", "10"))
STATIC_DIR = os.getenv("STATIC_DIR", "")              # folder with the built React site (set in the Docker image)
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "")        # shown in the privacy notice (grievance contact)
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "1"))  # proxies in front of the app (when TRUST_PROXY=true)
ALLOW_SQLITE_IN_PROD = os.getenv("ALLOW_SQLITE_IN_PROD", "false").lower() == "true"
