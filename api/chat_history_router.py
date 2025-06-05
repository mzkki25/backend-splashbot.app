from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from models.schemas import ChatHistory
from services.chat_history_service import ChatHistoryService
from api.deps import get_current_user

router = APIRouter()
chat_history_service = ChatHistoryService()


@router.get("", response_model=List[ChatHistory])
async def get_chat_history(user: Dict[str, Any] = Depends(get_current_user)) -> List[ChatHistory]:
    user_id: str = user['uid']
    return chat_history_service.fetch_chat_history(user_id)


@router.delete("/{session_id}", response_model=Dict[str, bool])
async def delete_chat(session_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, bool]:
    user_id: str = user['uid']
    return chat_history_service.delete_chat_session(user_id, session_id)


@router.delete("", response_model=Dict[str, bool])
async def clear_all_chats(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, bool]:
    user_id: str = user['uid']
    return chat_history_service.clear_all_user_chats(user_id)