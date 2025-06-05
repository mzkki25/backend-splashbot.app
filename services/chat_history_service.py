from typing import List, Dict
from fastapi import HTTPException, status

from models.schemas import ChatHistory
from core.firebase import db
from core.logging_logger import setup_logger

logger = setup_logger(__name__)


class ChatHistoryService:
    @staticmethod
    def fetch_chat_history(user_id: str) -> List[ChatHistory]:
        try:
            chats = db.collection('chats') \
                .where('user_id', '==', user_id) \
                .order_by('created_at', direction="DESCENDING") \
                .stream()

            logger.info(f"Fetching chat history for user: {user_id}")

            history: List[ChatHistory] = []
            for chat in chats:
                chat_data = chat.to_dict()
                history.append(
                    ChatHistory(
                        chat_session_id=chat.id,
                        title=chat_data['title'],
                        timestamp=chat_data['created_at'].isoformat() if chat_data['created_at'] else ""
                    )
                )

            logger.info(f"Chat history fetched successfully for user: {user_id}")
            return history

        except Exception as e:
            logger.error(f"Error fetching chat history for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    def delete_chat_session(user_id: str, session_id: str) -> Dict[str, bool]:
        try:
            chat_ref = db.collection("chats").document(session_id)
            chat_doc = chat_ref.get()

            logger.info(f"Deleting chat session: {session_id} for user: {user_id}")

            if not chat_doc.exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

            chat_data = chat_doc.to_dict()
            if chat_data.get("user_id") != user_id:
                logger.warning(f"Unauthorized access attempt to chat session: {session_id} by user: {user_id}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access")

            chat_ref.delete()
            return {"success": True}

        except Exception as e:
            logger.error(f"Error deleting chat session {session_id} for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @staticmethod
    def clear_all_user_chats(user_id: str) -> Dict[str, bool]:
        try:
            chats = db.collection("chats").where("user_id", "==", user_id).stream()

            logger.info(f"Clearing all chat sessions for user: {user_id}")

            for chat in chats:
                chat.reference.delete()

            logger.info(f"All chat sessions cleared for user: {user_id}")
            return {"success": True}

        except Exception as e:
            logger.error(f"Error clearing chat sessions for user {user_id}: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
