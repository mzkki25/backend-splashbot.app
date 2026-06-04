import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.chat import ChatSession
from models.message import Message
from schemas.chat import ChatMessageItem
from core.logger import setup_logger

logger = setup_logger(__name__)


class MessageController:
    @staticmethod
    async def get_messages(db: AsyncSession, user_id: str, session_id: str) -> list[ChatMessageItem]:
        session = await db.get(ChatSession, uuid.UUID(session_id))
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        if str(session.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")

        result = await db.execute(
            select(Message)
            .where(Message.chat_session_id == uuid.UUID(session_id))
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        return [
            ChatMessageItem(
                message_id=str(m.id),
                chat_session_id=str(m.chat_session_id),
                role=m.role,
                content=m.content,
                file_id=str(m.file_id) if m.file_id else None,
                timestamp=m.created_at.isoformat() if m.created_at else None,
                references=m.references,
            )
            for m in messages
        ]
