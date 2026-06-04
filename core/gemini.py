from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

from core.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

llm_code_gen = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,
    convert_system_message_to_human=True,
)

llm_analysis = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
    convert_system_message_to_human=True,
)

llm_multimodal = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
    convert_system_message_to_human=True,
)
