"""Rate-limit instances and helpers shared by the routers."""
import hashlib
import logging

from fastapi import HTTPException, Request

from . import config
from .ratelimit import RateLimiter

log = logging.getLogger("medimate.security")

register_limiter = RateLimiter(config.REGISTER_MAX_PER_HOUR, 3600)
login_ip_limiter = RateLimiter(config.LOGIN_MAX_PER_IP, 300)
login_fail_limiter = RateLimiter(config.LOGIN_MAX_FAILS, 900)


def reset_limiters():
    for lim in (register_limiter, login_ip_limiter, login_fail_limiter):
        lim.reset_all()


def client_ip(request: Request) -> str:
    if config.TRUST_PROXY:  # only trust this header when YOUR proxy sets it
        parts = [x.strip() for x in request.headers.get("x-forwarded-for", "").split(",") if x.strip()]
        if parts:
            # each trusted proxy appends the address it saw; count from the right so clients cannot fake it
            return parts[-min(config.TRUSTED_PROXY_HOPS, len(parts))]
    return request.client.host if request.client else "unknown"


def raise_if_blocked(limiter: RateLimiter, key: str, message: str):
    wait = limiter.seconds_until_allowed(key)
    if wait:
        raise HTTPException(429, message, headers={"Retry-After": str(wait)})


def anon(value: str) -> str:
    """Short hash so logs never contain raw emails."""
    return hashlib.sha256(value.encode()).hexdigest()[:10]
