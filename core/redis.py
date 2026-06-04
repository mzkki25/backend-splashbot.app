import redis.asyncio as aioredis

from core.config import REDIS_URL

redis_client: aioredis.Redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis_client
