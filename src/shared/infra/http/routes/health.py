from datetime import UTC

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from src.shared.infra.env.env_service import env_service
from src.shared.infra.persistence.session import async_session_factory

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    db_status = await _check_database()
    cache_status = await _check_redis()

    from datetime import datetime
    status = "ok" if db_status["status"] == "up" and cache_status["status"] == "up" else "degraded"

    return {
        "status": status,
        "timestamp": datetime.now(UTC).isoformat(),
        "db": db_status,
        "cache": cache_status,
    }


async def _check_database() -> dict:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "up"}
    except Exception as e:
        return {"status": "down", "error": str(e)}


async def _check_redis() -> dict:
    try:
        r = aioredis.from_url(env_service.redis_url)
        pong = await r.ping()
        await r.aclose()
        return {"status": "up" if pong else "down"}
    except Exception:
        return {"status": "down"}
