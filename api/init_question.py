from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from models.schemas import ChatInit

from utils.initial_question import initial_questions_gm, initial_questions_ngm

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.get("")
async def init_question(chat_option: str):
    try:
        if chat_option == "General Macroeconomics":
            init_questions = initial_questions_gm()
        else:
            init_questions = initial_questions_ngm(chat_option=chat_option) 

        logger.info(f"Initial questions fetched for chat option: {chat_option}")   

        return JSONResponse(content={
            "init_questions": init_questions,
        }, status_code=status.HTTP_200_OK)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))