import logging
from datetime import datetime, timezone
from fastapi import APIRouter
import redis.asyncio as aioredis
from app.core.config import settings
from app.schemas import CacheClearResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_server_cache():
    """Flush server-side Redis cache keys with graceful fallback."""
    now = utc_now()
    redis_url = (settings.REDIS_URL or "").strip()
    if not redis_url or redis_url.lower() in ("none", "disabled", "off"):
        logger.info("REDIS_URL not set or disabled; cache clear simulated.")
        return CacheClearResponse(status="cache_unavailable", flushed_at=now, keys_cleared=0)

    try:
        r = aioredis.from_url(redis_url, decode_responses=True)
        await r.flushdb()
        await r.aclose()
        logger.info("Redis cache flushed successfully via /cache/clear.")
        return CacheClearResponse(status="cleared", flushed_at=now, keys_cleared=0)
    except Exception as e:
        logger.warning(f"Failed to clear Redis cache: {e}")
        return CacheClearResponse(status="cache_unavailable", flushed_at=now, keys_cleared=0)
