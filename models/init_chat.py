from fastapi import HTTPException
from typing import List, Dict, Any, Tuple, Optional, Union, Literal

from core.firebase import db, bucket
from core.gemini import model_2, multimodal_model_2
from utils.semantic_search import (
    find_relevant_chunks_with_faiss, extract_pdf_text_by_page, 
    is_prompt_about_specific_table, find_pages_containing
)

from utils.makroeconomics import (
    two_wheels_model, four_wheels_model, retail_general_model,
    retail_beauty_model, retail_fnb_model, retail_drugstore_model
)
from utils.prompt.file_prompt import (
    handle_file_pdf, handle_file_image
)
from utils.prompt.web_prompt import handle_web_prompt
from utils.search_web import search_web_snippets
from utils.follow_up_question import (
    recommend_follow_up_questions_gm,
    recommend_follow_up_questions_ngm
)

from PIL import Image
from firebase_admin import firestore

import io
import uuid
import datetime

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

class Chat:
    def __init__(self):
        self.now = datetime.datetime.now(datetime.UTC)

    def init_or_update_chat(self, chat_session, user_id, prompt, file_id_input):
        chat_ref = db.collection('chats').document(chat_session)
        chat_doc = chat_ref.get()
        last_response = None

        if not chat_doc.exists:
            chat_title = prompt[:17] + "..." if len(prompt) > 17 else prompt
            chat_ref.set({
                'user_id': user_id,
                'title': chat_title,
                'status': 'active',
                'messages': [],
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_file_id': file_id_input,
                'last_response': None
            })
        else:
            chat_data = chat_doc.to_dict()
            last_response = chat_data.get("last_response")
            last_file_id = chat_data.get("last_file_id")

            if file_id_input and file_id_input != last_file_id:
                chat_ref.update({'last_file_id': file_id_input})
            elif not file_id_input and last_file_id:
                file_id_input = last_file_id

        return chat_ref, last_response, file_id_input

    async def generate_response(self, chat_option, prompt, file_id_input, last_response, user_id):
        file_url = None
        references = None

        if chat_option == "General Macroeconomics":
            if file_id_input:
                file_url, response = self._handle_file_prompt(prompt, file_id_input, last_response)
                follow_up_question = recommend_follow_up_questions_gm(prompt, response['explanation'], file_id_input)
            else:
                response, references = self._handle_web_prompt(prompt, last_response)
                follow_up_question = recommend_follow_up_questions_gm(prompt, response['explanation'])
        else:
            response = self._handle_custom_model(chat_option, prompt, user_id, last_response)
            follow_up_question = recommend_follow_up_questions_ngm(prompt, response['explanation'], chat_option)
            file_id_input = None

        return response, file_url, references, follow_up_question

    def _handle_file_prompt(self, prompt: str, file_id_input: str, last_response: str) -> Tuple[Optional[str], Dict[str, Any]]:
        file_doc = db.collection('files').document(file_id_input).get()
        if not file_doc.exists:
            raise HTTPException(status_code=404, detail="File not found")

        file_data = file_doc.to_dict()
        file_url = file_data.get('url')
        content_type = file_data.get('content_type')
        storage_path = file_data.get('storage_path')

        blob = bucket.blob(storage_path)
        file_content = blob.download_as_bytes()

        if 'application/pdf' in content_type:
            pdf_pages = extract_pdf_text_by_page(file_content)
            table_keyword = is_prompt_about_specific_table(prompt)

            if table_keyword:
                filtered_pages = find_pages_containing(pdf_pages, table_keyword)
                if filtered_pages:
                    logger.info(f"Table found in filtered pages.")
                    relevant_text = find_relevant_chunks_with_faiss(filtered_pages, prompt.lower(), chunk_size=4096, top_k=1)
                else:
                    logger.warning(f"Table not found in filtered pages, using all pages.")
                    relevant_text = find_relevant_chunks_with_faiss(pdf_pages, prompt.lower(), chunk_size=4096, top_k=1)
            else:
                logger.info(f"Table not found in prompt, using all pages.")
                relevant_text = find_relevant_chunks_with_faiss(pdf_pages, prompt.lower(), chunk_size=1024, top_k=5)
            
            response = model_2.generate_content(
                handle_file_pdf(prompt, relevant_text, last_response)
            ).text

        elif content_type.startswith('image/'):
            image = Image.open(io.BytesIO(file_content)).convert("RGB")
            response = multimodal_model_2.generate_content(
                handle_file_image(image, prompt, last_response)
            ).text

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        return file_url, {
            "explanation": response,
            "result": None
        }
    
    def _format_snippets(self, search_results) -> str:
        titles = search_results.get("list_title_results", [])
        links = search_results.get("list_linked_results", [])
        snippets = search_results.get("list_snippet_results", [])

        formatted = []
        for title, link, snippet in zip(titles, links, snippets):
            formatted.append(f"**{title}**\n{snippet}\n[Link]({link})\n")
            
        formatted = [f"**{i+1}.** {sentence}" for i, sentence in enumerate(formatted)]
        return "\n".join(formatted)

    def _handle_web_prompt(self, prompt, last_response) -> Tuple[Dict[str, Any], List[str]]:
        results = search_web_snippets(prompt, num_results=5)
        snippets    = self._format_snippets(results)
        references  = results.get("list_linked_results", [])

        response = model_2.generate_content(
            handle_web_prompt(last_response, prompt, snippets)
        ).text

        if response.__contains__("saya hanya dapat menjawab pertanyaan yang berkaitan dengan ekonomi"):
            references = None

        return {
            "explanation": response,
            "result": None
        }, references

    def _handle_custom_model(self, 
        chat_option: Union[Literal[
            "2 Wheels", "4 Wheels", "Retail General", 
            "Retail Beauty", "Retail FnB", "Retail Drugstore"
        ]],
        prompt: str, user_id: str, last_response: str
    ) -> Dict[str, Any]:
        model_map = {
            "2 Wheels": two_wheels_model,
            "4 Wheels": four_wheels_model,
            "Retail General": retail_general_model,
            "Retail Beauty": retail_beauty_model,
            "Retail FnB": retail_fnb_model,
            "Retail Drugstore": retail_drugstore_model
        }

        model_func = model_map.get(chat_option)
        if not model_func:
            raise HTTPException(status_code=400, detail="Invalid chat option")
        
        return model_func(prompt, user_id, last_response)

    def save_chat_messages(self, chat_ref, chat_session, prompt, response, file_id_input, references):
        chat_ref.update({
            'messages': firestore.ArrayUnion([
                {
                    'message_id': f"user-{uuid.uuid4()}",
                    'chat_session_id': chat_session,
                    'role': 'user',
                    'content': prompt,
                    'file_id': file_id_input,
                    'created_at': datetime.datetime.now(datetime.UTC),
                },
                {
                    'message_id': f"assistant-{uuid.uuid4()}",
                    'chat_session_id': chat_session,
                    'role': 'assistant',
                    'content': response,
                    'created_at': datetime.datetime.now(datetime.UTC),
                    'references': references,
                }
            ]),
            'last_response': response['explanation'],
        })