"""
Rate limiting via slowapi, backed by Redis (not in-memory) so the limit is
shared across every backend instance — an in-memory limiter would let each
instance enforce its own separate quota, which defeats the point the moment
you run more than one instance behind a load balancer.

`limiter.enabled` is flipped off for the test suite (see tests/conftest.py)
so the existing tests' normal call volume doesn't trip production-strength
limits; a dedicated test re-enables it to prove the limiting itself works.
"""
from fastapi import Request
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.security import decode_access_token
from app.config import settings

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)


def user_or_ip_key(request: Request) -> str:
    """
    Rate-limit key for authenticated endpoints: bucket by the authenticated
    user's id rather than IP, so the quota follows the account, not the
    network. Falls back to IP if there's no valid token — the route's own
    auth dependency rejects the request either way, this only affects which
    bucket an abuse attempt lands in.
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except JWTError:
            pass
    return f"ip:{get_remote_address(request)}"
