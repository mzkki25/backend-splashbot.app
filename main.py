from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (
    auth_router, chat_router, file_upload_router, 
    chat_history_router, chat_messages_router, init_question
)

import uvicorn

app = FastAPI(title="SPLASHBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(file_upload_router.router, prefix="/upload", tags=["File Upload"])
app.include_router(chat_router.router, prefix="/chat", tags=["Chat"])
app.include_router(chat_history_router.router, prefix="/history", tags=["History"])
app.include_router(chat_messages_router.router, prefix="/{chat_session}/messages", tags=["Messages"])
app.include_router(init_question.router, prefix="/init_questions", tags=["Initial Questions"])

if __name__ == "__main__":
    import os
    uvicorn.run(port=int(os.environ.get("PORT", 8000)), host='0.0.0.0')