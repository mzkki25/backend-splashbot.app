from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any, Dict

from models.schemas import ChatRequest, ChatResponse
from services.chat_service import ChatService
from api.deps import get_current_user

router = APIRouter()
chat_service = ChatService()


@router.post("/{chat_session}", response_model=ChatResponse)
async def process_chat(
    chat_session: str,
    chat_request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    try:
        user_id: str = user["uid"]
        response_data: Dict[str, Any] = await chat_service.process_chat_session(
            chat_session, user_id, chat_request
        )

        return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

    except Exception as e:
        from core.logging_logger import setup_logger
        logger = setup_logger(__name__)
        logger.error(f"Error processing chat session {chat_session}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))