from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from api import (
    auth_router,
    chat_router,
    file_upload_router,
    chat_history_router,
    chat_messages_router,
    init_question,
)
from core.database import init_db
from core.config import UPLOAD_DIR
from core.logger import get_logger
import os

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SPLASHBot API...")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    await init_db()
    logger.info("SPLASHBot API ready")
    yield
    logger.info("Shutting down SPLASHBot API")


app = FastAPI(title="SPLASHBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(file_upload_router.router, prefix="/upload", tags=["File Upload"])
app.include_router(chat_router.router, prefix="/chat", tags=["Chat"])
app.include_router(chat_history_router.router, prefix="/history", tags=["History"])
app.include_router(chat_messages_router.router, prefix="/{chat_session}/messages", tags=["Messages"])
app.include_router(init_question.router, prefix="/init_questions", tags=["Initial Questions"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=int(os.environ.get("PORT", 8000)), host="0.0.0.0")
