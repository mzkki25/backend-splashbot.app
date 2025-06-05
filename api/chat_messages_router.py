from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from models.schemas import ChatMessage
from services.chat_message_service import ChatMessageService
from api.deps import get_current_user

router = APIRouter()
chat_message_service = ChatMessageService()


@router.get("", response_model=List[ChatMessage])
async def get_chat_messages(
    chat_session: str,
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[ChatMessage]:
    user_id: str = user['uid']
    return chat_message_service.get_messages(chat_session, user_id)
