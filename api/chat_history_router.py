from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import ChatHistoryItem, RenameChatRequest
from controllers.history_controller import HistoryController
from api.deps import get_current_user
from core.database import get_db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=List[ChatHistoryItem])
async def get_chat_history(
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChatHistoryItem]:
    logger.info(f"Fetching chat history for user {user['uid']}")
    return await HistoryController.get_history(db, user["uid"])


@router.delete("/{session_id}")
async def delete_chat(
    session_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    logger.info(f"Deleting chat session {session_id} for user {user['uid']}")
    return await HistoryController.delete_session(db, user["uid"], session_id)


@router.delete("")
async def clear_all_chats(
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    logger.info(f"Clearing all chats for user {user['uid']}")
    return await HistoryController.clear_all(db, user["uid"])


@router.patch("/{session_id}")
async def rename_chat(
    session_id: str,
    body: RenameChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    logger.info(f"Renaming chat session {session_id} to '{body.title}' for user {user['uid']}")
    return await HistoryController.rename_session(db, user["uid"], session_id, body.title)
