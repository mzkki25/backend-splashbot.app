from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

from core.config import GEMINI_API_KEY
from core.logger import get_logger

logger = get_logger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

llm_code_gen = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.6,
)

llm_analysis = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.6,
)

llm_multimodal = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.6,
)

logger.info("Gemini models initialized: gemini-3-flash-preview")
