from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import ChatRequest, ChatResponse
from api.deps import get_current_user
from models.init_chat import Chat

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()
chat_handler = Chat()

@router.post("/{chat_session}", response_model=ChatResponse)
async def process_chat(chat_session: str, chat_request: ChatRequest, user=Depends(get_current_user)):
    try:
        user_id = user['uid']
        prompt = chat_request.prompt
        file_id_input = chat_request.file_id

        chat_ref, last_response, file_id_input = chat_handler.init_or_update_chat(
            chat_session, user_id, prompt, file_id_input
        )

        logger.info(f"Chat session initialized/updated: {chat_session}")

        response, file_url, references, follow_up_question = await chat_handler.generate_response(
            chat_request.chat_options, prompt, file_id_input, last_response, user_id
        )

        logger.info(f"Response generated for chat session: {chat_session}")

        chat_handler.save_chat_messages(
            chat_ref, chat_session, prompt, response, file_id_input, references
        )

        logger.info(f"Chat messages saved for session: {chat_session}")

        return JSONResponse(content={
            "response": response,
            "file_url": file_url,
            "created_at": chat_handler.now.isoformat(),
            "references": references,
            "follow_up_question": follow_up_question,
        }, status_code=200)

    except Exception as e:
        logger.error(f"Error processing chat session {chat_session}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
