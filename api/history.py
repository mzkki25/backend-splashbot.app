from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import ChatHistory, ChatMessage
from core.firebase import db
from api.deps import get_current_user
from typing import List, Dict

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.get("", response_model=List[ChatHistory])
async def get_chat_history(user = Depends(get_current_user)):
    try:
        user_id = user['uid']

        chats = db.collection('chats').where('user_id', '==', user_id).order_by('created_at', direction="DESCENDING").stream()

        logger.info(f"Fetching chat history for user: {user_id}")

        history = []
        for chat in chats:
            chat_data = chat.to_dict()
            history.append(
                ChatHistory(
                    chat_session_id=chat.id,
                    title=chat_data['title'],
                    timestamp=chat_data['created_at'].isoformat() if chat_data['created_at'] else ""
                ))
            
        logger.info(f"Chat history fetched successfully for user: {user_id}")

        return history
    except Exception as e:
        logger.error(f"Error fetching chat history for user {user['uid']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{session_id}", response_model=Dict[str, bool])
async def delete_chat(session_id: str, user=Depends(get_current_user)):
    try:
        user_id = user['uid']
        chat_ref = db.collection("chats").document(session_id)
        chat_doc = chat_ref.get()

        logger.info(f"Deleting chat session: {session_id} for user: {user_id}")

        if not chat_doc.exists:
            raise HTTPException(status_code=404, detail="Chat not found")

        chat_data = chat_doc.to_dict()
        if chat_data.get("user_id") != user_id:
            logger.warning(f"Unauthorized access attempt to chat session: {session_id} by user: {user_id}")
            raise HTTPException(status_code=403, detail="Unauthorized access")

        chat_ref.delete()

        return {"success": True}

    except Exception as e:
        logger.error(f"Error deleting chat session {session_id} for user {user['uid']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("", response_model=Dict[str, bool])
async def clear_all_chats(user=Depends(get_current_user)):
    try:
        user_id = user['uid']
        chats_ref = db.collection("chats").where("user_id", "==", user_id)
        chats = chats_ref.stream()

        logger.info(f"Clearing all chat sessions for user: {user_id}")

        for chat in chats:
            chat.reference.delete()

        logger.info(f"All chat sessions cleared for user: {user_id}")

        return {"success": True}
    except Exception as e:
        logger.error(f"Error clearing chat sessions for user {user['uid']}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))