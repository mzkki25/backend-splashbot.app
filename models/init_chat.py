from fastapi import HTTPException

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

    def _handle_file_prompt(self, prompt, file_id_input, last_response):
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
                f"""
                    Kamu adalah **SPLASHBot**, AI Agent yang mengkhususkan diri dalam **analisis dokumen ekonomi**, khususnya file **PDF** yang diberikan oleh pengguna.

                    ### Informasi yang Disediakan:
                    - **Pertanyaan dari pengguna**:  
                    "{prompt}"

                    - **Konten relevan dari PDF**:  
                    {relevant_text}

                    - **Respons terakhir dari percakapan sebelumnya**:  
                    {last_response}

                    ### Aturan Penting:
                    1. **Hanya jawab pertanyaan** jika isi PDF berkaitan dengan **ekonomi**.
                    2. Soroti **kata kunci penting** dalam jawaban dengan **bold** agar mudah dikenali.
                    3. Jawaban harus **jelas**, **fokus pada konteks ekonomi**, dan **berdasarkan isi PDF**.
                    4. Buatlah kesimpulan dan rekomendasi yang **bernilai insight** dirangkum ke dalam poin-poin.

                    ### Tugas:
                    Berikan jawaban berbasis analisis isi PDF tersebut, dengan tetap menjaga fokus pada aspek ekonomi dan pertanyaan pengguna.
                """
            ).text

        elif content_type.startswith('image/'):
            image = Image.open(io.BytesIO(file_content)).convert("RGB")
            response = multimodal_model_2.generate_content(
               [
                    "Kamu adalah **SPLASHBot**, AI analis yang **mengkhususkan diri di bidang ekonomi dan bisnis**, serta mampu **menganalisis gambar** yang relevan dengan topik tersebut.",
                    image,
                    f"""
                        ### Konteks:

                        - Pertanyaan dari pengguna: **{prompt}**
                        - Respon terakhir dalam percakapan sebelumnya:  
                        {last_response}

                        ### Instruksi:

                        1. Tinjau gambar yang diberikan.
                        2. Jika **gambar tidak berkaitan dengan topik ekonomi atau bisnis**, **jangan memberikan jawaban apapun** selain menyatakan bahwa gambar tidak relevan.
                        3. Jika gambar relevan, berikan **analisis ekonomi atau bisnis yang tajam dan bernilai**.
                        4. Soroti **kata kunci penting** dalam jawaban dengan format **bold** untuk penekanan.
                        5. Jawaban harus **padat, profesional, dan bernilai insight**—hindari narasi yang terlalu panjang atau di luar topik.

                        ### Tujuan:
                        Memberikan analisis **berbasis visual** dengan fokus pada **makna ekonomi**, seperti tren pasar, perilaku konsumen, pertumbuhan, distribusi wilayah, dsb.
                    """
                ]
            ).text

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        return file_url, {
            "explanation": response,
            "result": None
        }
    
    def _format_snippets(self, search_results):
        titles = search_results.get("list_title_results", [])
        links = search_results.get("list_linked_results", [])
        snippets = search_results.get("list_snippet_results", [])

        formatted = []
        for title, link, snippet in zip(titles, links, snippets):
            formatted.append(f"**{title}**\n{snippet}\n[Link]({link})\n")
            
        formatted = [f"**{i+1}.** {sentence}" for i, sentence in enumerate(formatted)]
        return "\n".join(formatted)

    def _handle_web_prompt(self, prompt, last_response):
        results = search_web_snippets(prompt, num_results=5)
        snippets    = self._format_snippets(results)
        references  = results.get("list_linked_results", [])

        response = model_2.generate_content(
            f"""
            Kamu adalah **SPLASHBot**, sebuah AI Agent yang ahli dalam menjawab pertanyaan seputar **ekonomi**, termasuk ekonomi makro, mikro, kebijakan fiskal/moneter, perdagangan, keuangan, dan indikator ekonomi.

            ### Konteks Sebelumnya:
            {last_response}

            ### Pertanyaan dari Pengguna:
            {prompt}

            ### Informasi dari Internet:
            {snippets}

            ### Catatan Penting:
            - Gunakan informasi dari internet dan pengetahuan terkini jika relevan dengan topik ekonomi.
            - Abaikan informasi yang tidak berkaitan dengan ekonomi.
            - Sisipkan tautan referensi secara **implisit dan alami ke dalam kalimat**, seperti gaya ChatGPT. Contoh:  
              - _Produk Domestik Bruto (PDB) [Merupakan salah satu indikator terpenting yang mengukur total nilai barang dan jasa yang](https://www.metrotvnews.com/read/koGCR6qv-memahami-produk-domestik-bruto-dan-pentingnya-bagi-perekonomian)..._,  
              - _positif dengan pertumbuhan ekonomi dalam jangka panjang [mungkin karena investasi pemerintah yang strategis](https://ejournal.uinib.ac.id/febi/index.php/maqdis/article/download/501/385)..._.
            - Gunakan **penekanan (bold)** pada kata kunci penting agar poin-poin penting mudah dikenali.
            - Hindari menjawab dengan "saya tidak tahu" atau "saya tidak bisa menjawab".
            - Gunakan data atau pengetahuan yang tersedia untuk memberikan jawaban yang **informatif**, **jelas**, dan **relevan**.

            ### Tugasmu:
            Berikan jawaban yang **jelas**, **relevan**, dan **berbasis ekonomi** terhadap pertanyaan pengguna. 
            Jika pertanyaannya **tidak berkaitan dengan ekonomi**, cukup balas dengan: _"Maaf, saya hanya dapat menjawab pertanyaan yang berkaitan dengan ekonomi."_
            """
        ).text

        if response.__contains__("saya hanya dapat menjawab pertanyaan yang berkaitan dengan ekonomi"):
            references = None

        return {
            "explanation": response,
            "result": None
        }, references

    def _handle_custom_model(self, chat_option, prompt, user_id, last_response):
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