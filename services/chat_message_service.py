from typing import List, Dict, Any
from fastapi import HTTPException, status

from models.schemas import ChatMessage
from core.firebase import db
from core.logging_logger import setup_logger

logger = setup_logger(__name__)


class ChatMessageService:
    @staticmethod
    def get_messages(chat_session_id: str, user_id: str) -> List[ChatMessage]:
        try:
            chat_ref = db.collection('chats').document(chat_session_id)
            chat_doc = chat_ref.get()

            logger.info(f"Fetching chat messages for session: {chat_session_id} for user: {user_id}")

            if not chat_doc.exists:
                logger.warning(f"Chat session not found: {chat_session_id} for user: {user_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

            chat_data: Dict[str, Any] = chat_doc.to_dict()

            if chat_data.get('user_id') != user_id:
                logger.warning(f"Unauthorized access attempt to chat session: {chat_session_id} by user: {user_id}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to chat")

            messages: List[Dict[str, Any]] = chat_data.get('messages', [])

            results: List[ChatMessage] = []
            for msg in messages:
                created_at = msg.get('created_at')
                timestamp_str = created_at.isoformat() if created_at else ""

                results.append(
                    ChatMessage(
                        message_id=msg.get('message_id', ''),
                        chat_session_id=chat_session_id,
                        role=msg.get('role', ''),
                        content=msg.get('content', ''),
                        file_id=msg.get('file_id'),
                        timestamp=timestamp_str,
                        references=msg.get('references', [])
                    )
                )

            logger.info(f"Chat messages fetched successfully for session: {chat_session_id} for user: {user_id}")
            return results

        except Exception as e:
            logger.error(f"Error fetching chat messages for session {chat_session_id} for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
