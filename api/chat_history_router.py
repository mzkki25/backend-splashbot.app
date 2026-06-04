from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import ChatHistoryItem
from controllers.history_controller import HistoryController
from api.deps import get_current_user
from core.database import get_db

router = APIRouter()


@router.get("", response_model=List[ChatHistoryItem])
async def get_chat_history(
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatHistoryItem]:
    return await HistoryController.get_history(db, user["uid"])


@router.delete("/{session_id}")
async def delete_chat(
    session_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    return await HistoryController.delete_session(db, user["uid"], session_id)


@router.delete("")
async def clear_all_chats(
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    return await HistoryController.clear_all(db, user["uid"])
