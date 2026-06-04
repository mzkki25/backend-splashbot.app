from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

from core.config import REDIS_URL

_redis_store: dict[str, RedisChatMessageHistory] = {}


def get_message_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in _redis_store:
        _redis_store[session_id] = RedisChatMessageHistory(
            session_id=f"chat:{session_id}",
            url=REDIS_URL,
            ttl=86400,
        )
    return _redis_store[session_id]


def set_agent_memory(session_id: str, key: str, value: str, ttl: int = 86400):
    import redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.set(f"agent:{session_id}:{key}", value, ex=ttl)


def get_agent_memory(session_id: str, key: str) -> str | None:
    import redis
    r = redis.from_url(REDIS_URL, decode_responses=True)
    return r.get(f"agent:{session_id}:{key}")
