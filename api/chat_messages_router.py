from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import ChatMessageItem
from controllers.message_controller import MessageController
from api.deps import get_current_user
from core.database import get_db

router = APIRouter()


@router.get("", response_model=List[ChatMessageItem])
async def get_chat_messages(
    chat_session: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatMessageItem]:
    return await MessageController.get_messages(db, user["uid"], chat_session)
