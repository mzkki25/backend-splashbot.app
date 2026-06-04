import redis.asyncio as aioredis

from core.config import REDIS_URL
from core.logger import get_logger

logger = get_logger(__name__)

redis_client: aioredis.Redis = aioredis.from_url(REDIS_URL, decode_responses=True)
logger.info(f"Redis client initialized: {REDIS_URL}")


async def get_redis():
    return redis_client
