from fastapi import APIRouter, Depends, HTTPException
from models.schemas import ChatHistory, ChatMessage
from core.firebase import db
from api.deps import get_current_user
from typing import List

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.get("", response_model=List[ChatMessage])
async def get_chat_messages(chat_session: str, user=Depends(get_current_user)):
    try:
        user_id = user['uid']

        chat_ref = db.collection('chats').document(chat_session)
        chat_doc = chat_ref.get()

        logger.info(f"Fetching chat messages for session: {chat_session} for user: {user_id}")

        if not chat_doc.exists:
            logger.warning(f"Chat session not found: {chat_session} for user: {user_id}")
            raise HTTPException(status_code=404, detail="Chat not found")

        chat_data = chat_doc.to_dict()

        if chat_data['user_id'] != user_id:
            logger.warning(f"Unauthorized access attempt to chat session: {chat_session} by user: {user_id}")
            raise HTTPException(status_code=403, detail="Unauthorized access to chat")

        messages = chat_data.get('messages', [])

        results = []
        for msg in messages:
            created_at = msg.get('created_at')
            timestamp_str = created_at.isoformat()

            results.append(
                ChatMessage(
                    message_id=msg.get('message_id', ''),
                    chat_session_id=chat_session,
                    role=msg.get('role', ''),
                    content=msg.get('content', ''),
                    file_id=msg.get('file_id'),
                    timestamp=timestamp_str,
                    references=msg.get('references', [])
                ))
            
        logger.info(f"Chat messages fetched successfully for session: {chat_session} for user: {user_id}")

        return results

    except Exception as e:
        logger.error(f"Error fetching chat messages for session {chat_session} for user {user['uid']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))