from typing import Any, Dict, Tuple
from models.schemas import ChatRequest
from models.init_chat import Chat

from core.logging_logger import setup_logger

logger = setup_logger(__name__)


class ChatService:
    def __init__(self):
        self.chat_handler = Chat()

    async def process_chat_session(
        self, chat_session: str, user_id: str, chat_request: ChatRequest
    ) -> Dict[str, Any]:
        prompt: str = chat_request.prompt
        file_id_input: str = chat_request.file_id

        chat_ref, last_response, file_id_input = self.chat_handler.init_or_update_chat(
            chat_session, user_id, prompt, file_id_input
        )
        logger.info(f"Chat session initialized/updated: {chat_session}")

        response, file_url, references, follow_up_question = await self.chat_handler.generate_response(
            chat_request.chat_options, prompt, file_id_input, last_response, user_id
        )
        logger.info(f"Response generated for chat session: {chat_session}")

        self.chat_handler.save_chat_messages(
            chat_ref, chat_session, prompt, response, file_id_input, references
        )
        logger.info(f"Chat messages saved for session: {chat_session}")

        return {
            "response": response,
            "file_url": file_url,
            "created_at": self.chat_handler.now.isoformat(),
            "references": references,
            "follow_up_question": follow_up_question,
        }
