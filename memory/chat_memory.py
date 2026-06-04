from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

from core.config import REDIS_URL
from core.logger import get_logger

logger = get_logger(__name__)

_redis_store: dict[str, RedisChatMessageHistory] = {}
TTL = 86400


def _get_history(session_id: str) -> RedisChatMessageHistory:
    if session_id not in _redis_store:
        _redis_store[session_id] = RedisChatMessageHistory(
            session_id=f"chat:{session_id}",
            url=REDIS_URL,
            ttl=TTL,
        )
        logger.debug(f"Created new RedisChatMessageHistory for session {session_id}")
    return _redis_store[session_id]


def get_conversation_context(session_id: str) -> str:
    history = _get_history(session_id)
    messages = history.messages
    if not messages:
        return ""
    lines = []
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        lines.append(f"{role}: {msg.content}")
    logger.debug(f"Retrieved {len(messages)} messages from Redis for session {session_id}")
    return "\n".join(lines)


def save_turn(session_id: str, user_msg: str, assistant_msg: str):
    history = _get_history(session_id)
    history.add_messages([
        HumanMessage(content=user_msg),
        AIMessage(content=assistant_msg),
    ])
    logger.debug(f"Saved turn to Redis for session {session_id}")


def clear_session(session_id: str):
    history = _get_history(session_id)
    history.clear()
    _redis_store.pop(session_id, None)
    logger.info(f"Cleared Redis session {session_id}")
