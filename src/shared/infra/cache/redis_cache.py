import json
import logging
from typing import Any

import redis.asyncio as aioredis
from fastapi.encoders import jsonable_encoder

from src.shared.infra.env.env_service import env_service

logger = logging.getLogger(__name__)

_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            env_service.redis_url,
            decode_responses=True,
        )
    return _pool


async def cache_get(key: str) -> Any | None:
    """Get a value from Redis cache. Returns None on miss or error."""
    try:
        r = _get_redis()
        value = await r.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        logger.warning("Cache get failed for key '%s'", key, exc_info=True)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Set a value in Redis cache with TTL (default 5 minutes)."""
    try:
        r = _get_redis()
        await r.set(key, json.dumps(jsonable_encoder(value)), ex=ttl_seconds)
    except Exception:
        logger.warning("Cache set failed for key '%s'", key, exc_info=True)


async def cache_delete(pattern: str) -> None:
    """Delete all keys matching a pattern."""
    try:
        r = _get_redis()
        keys = []
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await r.delete(*keys)
            logger.info("Invalidated %d cache keys matching '%s'", len(keys), pattern)
    except Exception:
        logger.warning("Cache delete failed for pattern '%s'", pattern, exc_info=True)


async def cache_delete_key(key: str) -> None:
    """Delete a single cache key."""
    try:
        r = _get_redis()
        await r.delete(key)
    except Exception:
        logger.warning("Cache delete failed for key '%s'", key, exc_info=True)
