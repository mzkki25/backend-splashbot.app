from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import ChatRequest
from controllers.chat_controller import ChatController
from api.deps import get_current_user
from core.database import get_db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/{chat_session}")
async def process_chat(
    chat_session: str,
    chat_request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        user_id: str = user["uid"]
        logger.info(f"Chat request: session={chat_session}, user={user_id}, option={chat_request.chat_options}")
        response_data = await ChatController.process_chat(
            db, user_id, chat_session, chat_request
        )
        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Chat processing error: session={chat_session}, error={e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
