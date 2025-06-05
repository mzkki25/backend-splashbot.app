import pdfplumber
import re
import numpy as np
import faiss
import langdetect
import io

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip().lower()

def is_prompt_about_specific_table(prompt: str) -> str | None:
    match = re.search(r"(tabel\s+\d+\.\d+|tabel\s+\d+|table\s+\d+\.\d+|table\s+\d+)", prompt.lower())
    return match.group(1).lower().replace("table", "tabel") if match else None

def extract_pdf_text_by_page(file_path: str) -> list:
    pages_text = []
    with pdfplumber.open(io.BytesIO(file_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            tables = page.extract_tables()
            for table in tables:
                if table:
                    for row in table:
                        text += "\n" + " | ".join(cell if cell else "" for cell in row)
            pages_text.append(text.strip().lower())
    return pages_text

def find_pages_containing(pages: list, keyword: str) -> list:
    keyword = normalize_text(keyword)
    return [page for page in pages if keyword in normalize_text(page)]

def safe_detect_lang(text: str, default: str = "id") -> str:
    try:
        return langdetect.detect(text)
    except langdetect.lang_detect_exception.LangDetectException:
        return default

def find_relevant_chunks_with_faiss(texts: list, query: str, chunk_size: int = 500, top_k: int = 3) -> str:
    chunks = []

    query_lang_detect = safe_detect_lang(query)
    texts_lang_detect = [safe_detect_lang(text) for text in texts if text.strip()]
    
    if not texts_lang_detect:
        logger.warning("No valid texts for language detection. Defaulting to 'id'.")
        texts_lang_detect_common = "id"
    else:
        texts_lang_detect_common = max(set(texts_lang_detect), key=texts_lang_detect.count)

    logger.info(f"Query language detected: {query_lang_detect}")
    logger.info(f"Texts language detected: {texts_lang_detect}")

    if query_lang_detect != texts_lang_detect_common:
        try:
            from googletrans import Translator
            translator = Translator()
            
            query = translator.translate(query, dest=texts_lang_detect_common).text
            logger.info(f"Translated query: {query}")
        except Exception as e:
            logger.warning(f"Translation failed: {e}")

    for text in texts:
        if text.strip(): 
            chunks.extend([text[i:i+chunk_size] for i in range(0, len(text), chunk_size)])

    if not chunks:
        logger.warning("No chunks generated from texts.")
        return ""

    chunk_embeddings = sentence_model.encode(chunks, normalize_embeddings=True).astype(np.float32)
    query_embeddings = sentence_model.encode([query], normalize_embeddings=True).astype(np.float32)

    dim = chunk_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  
    index.add(chunk_embeddings)

    distances, indices = index.search(query_embeddings, top_k)
    relevant_text = "\n\n".join([chunks[i] for i in indices[0]])
    return relevant_text

# def find_relevant_chunks_with_cosim(texts: list, query: str, chunk_size: int = 500, top_k: int = 3) -> str: 
#     chunks = []

#     query_lang_detect = safe_detect_lang(query)
#     texts_lang_detect = [safe_detect_lang(text) for text in texts if text.strip()]
    
#     if not texts_lang_detect:
#         logger.warning("No valid texts for language detection. Defaulting to 'id'.")
#         texts_lang_detect_common = "id"
#     else:
#         texts_lang_detect_common = max(set(texts_lang_detect), key=texts_lang_detect.count)

#     logger.info(f"Query language detected: {query_lang_detect}")
#     logger.info(f"Texts language detected: {texts_lang_detect}")

#     if query_lang_detect != texts_lang_detect_common:
#         try:
#             query = translator.translate(query, dest=texts_lang_detect_common).text
#             logger.info(f"Translated query: {query}")
#         except Exception as e:
#             logger.warning(f"Translation failed: {e}")

#     for text in texts:
#         if text.strip():  # Hindari text kosong
#             chunks.extend([text[i:i+chunk_size] for i in range(0, len(text), chunk_size)])

#     if not chunks:
#         logger.warning("No chunks generated from texts.")
#         return ""

#     chunk_embeddings = sentence_model.encode(chunks)
#     query_embedding = sentence_model.encode(query)

#     similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
#     top_indices = similarities.argsort()[-top_k:][::-1]

#     relevant_text = "\n\n".join([chunks[i] for i in top_indices])
#     return relevant_text