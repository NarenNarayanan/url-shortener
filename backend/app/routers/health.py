"""
Health check endpoint.

Deliberately checks real dependencies (Postgres, Redis) rather than returning
a hardcoded 200. A liveness check that doesn't verify its dependencies will
report "healthy" while the database is unreachable — exactly the moment you
need it to tell the truth. Deployment platforms (Render/Fly/Railway) and load
balancers use this endpoint to decide whether to route traffic to this instance.
"""
import logging

from fastapi import APIRouter, Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.cache import get_redis
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)) -> dict:
    status_report = {"status": "ok", "database": "unknown", "redis": "unknown"}

    try:
        db.execute(text("SELECT 1"))
        status_report["database"] = "ok"
    except Exception as exc:
        logger.exception("Database health check failed")
        status_report["database"] = "unreachable"
        status_report["status"] = "degraded"

    try:
        redis_client.ping()
        status_report["redis"] = "ok"
    except Exception as exc:
        logger.exception("Redis health check failed")
        status_report["redis"] = "unreachable"
        status_report["status"] = "degraded"

    return status_report
