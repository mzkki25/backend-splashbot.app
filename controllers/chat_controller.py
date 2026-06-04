import uuid
from datetime import datetime, timezone

from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.user import User
from models.chat import ChatSession
from models.message import Message
from schemas.chat import ChatRequest
from agents.graph import run_agent
from core.logger import setup_logger

logger = setup_logger(__name__)


class ChatController:
    @staticmethod
    async def process_chat(
        db: AsyncSession,
        user_id: str,
        chat_session_id: str,
        chat_request: ChatRequest,
    ) -> dict:
        prompt = chat_request.prompt
        file_id = chat_request.file_id
        chat_option = chat_request.chat_options

        chat_session = await db.get(ChatSession, uuid.UUID(chat_session_id))
        last_response = None
        last_file_id = None

        if not chat_session:
            title = prompt[:17] + "..." if len(prompt) > 17 else prompt
            chat_session = ChatSession(
                id=uuid.UUID(chat_session_id),
                user_id=uuid.UUID(user_id),
                title=title,
                chat_option=chat_option,
                last_file_id=uuid.UUID(file_id) if file_id else None,
                status="active",
            )
            db.add(chat_session)
            await db.commit()
        else:
            if chat_session.user_id != uuid.UUID(user_id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")
            last_response = chat_session.last_response
            last_file_id = str(chat_session.last_file_id) if chat_session.last_file_id else None

            if file_id and file_id != last_file_id:
                chat_session.last_file_id = uuid.UUID(file_id)
            elif not file_id and last_file_id:
                file_id = last_file_id
            await db.commit()

        result = await run_agent(
            session_id=chat_session_id,
            user_id=user_id,
            prompt=prompt,
            chat_option=chat_option,
            file_id=file_id,
        )

        user_msg = Message(
            chat_session_id=uuid.UUID(chat_session_id),
            role="user",
            content=prompt,
            file_id=uuid.UUID(file_id) if file_id else None,
        )
        db.add(user_msg)

        assistant_msg = Message(
            chat_session_id=uuid.UUID(chat_session_id),
            role="assistant",
            content=result["response"],
            references=result.get("references"),
        )
        db.add(assistant_msg)

        chat_session.last_response = result["response"]
        await db.commit()

        return {
            "response": result["response"],
            "file_url": result.get("file_url"),
            "created_at": result["created_at"],
            "references": result.get("references", []),
            "follow_up_question": result.get("follow_up_question"),
        }
