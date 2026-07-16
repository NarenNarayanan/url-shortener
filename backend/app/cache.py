"""
Redis client — single shared connection pool for the whole app.

`decode_responses=True` means we get plain Python strings back instead of bytes,
which keeps the calling code (services/routers) free of `.decode()` calls.
"""
import redis

from app.config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)


def get_redis() -> redis.Redis:
    """FastAPI dependency for injecting the Redis client into routes/services."""
    return redis_client
