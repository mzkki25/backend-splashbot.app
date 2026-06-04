import uuid

from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.chat import ChatSession
from schemas.chat import ChatHistoryItem
from core.logger import setup_logger

logger = setup_logger(__name__)


class HistoryController:
    @staticmethod
    async def get_history(db: AsyncSession, user_id: str) -> list[ChatHistoryItem]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == uuid.UUID(user_id))
            .order_by(desc(ChatSession.created_at))
        )
        sessions = result.scalars().all()
        return [
            ChatHistoryItem(
                chat_session_id=str(s.id),
                title=s.title,
                timestamp=s.created_at.isoformat() if s.created_at else "",
            )
            for s in sessions
        ]

    @staticmethod
    async def delete_session(db: AsyncSession, user_id: str, session_id: str) -> dict:
        session = await db.get(ChatSession, uuid.UUID(session_id))
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
        if str(session.user_id) != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")
        await db.delete(session)
        await db.commit()
        return {"success": True}

    @staticmethod
    async def clear_all(db: AsyncSession, user_id: str) -> dict:
        await db.execute(
            delete(ChatSession).where(ChatSession.user_id == uuid.UUID(user_id))
        )
        await db.commit()
        return {"success": True}
