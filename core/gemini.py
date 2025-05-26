import google.generativeai as genai
from core.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash-002')
multimodal_model = genai.GenerativeModel('gemini-1.5-flash-002')

model_2 = genai.GenerativeModel('gemini-2.0-flash')
multimodal_model_2 = genai.GenerativeModel('gemini-2.0-flash')