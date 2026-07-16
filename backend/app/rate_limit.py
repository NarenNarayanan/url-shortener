"""
Rate limiting via slowapi, backed by Redis (not in-memory) so the limit is
shared across every backend instance — an in-memory limiter would let each
instance enforce its own separate quota, which defeats the point the moment
you run more than one instance behind a load balancer.

`limiter.enabled` is flipped off for the test suite (see tests/conftest.py)
so the existing tests' normal call volume doesn't trip production-strength
limits; a dedicated test re-enables it to prove the limiting itself works.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
