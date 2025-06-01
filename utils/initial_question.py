from core.gemini import model
from utils.search_web import search_web_snippets
from utils.prompt.initial_question_prompt import (
    init_question_gm, init_question_2wheels
)

import pandas as pd
import numpy as np
import os

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

def initial_questions_gm(file_id_input=None):
    if file_id_input:
        return []
    else:
        initial_question = "Apa saja hal-hal utama yang dipelajari dalam ekonomi makro dan bagaimana pengaruhnya terhadap perekonomian suatu negara?"
        web_context = search_web_snippets(initial_question)['snippet_results']

        prompt = init_question_gm(initial_question, web_context)

        response = eval(model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip())

        num_questions = np.random.randint(3, 6)
        if len(response) > num_questions:
            response = np.random.choice(response, num_questions, replace=False).tolist()

        return response

def initial_questions_ngm(chat_option):
    if chat_option == "2 Wheels":
        try:
            df = pd.read_csv('dataset/2_wheels.csv')

            prompt = init_question_2wheels(df)

            response = eval(model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip())
            num_questions = np.random.randint(3, 6)

            if len(response) > num_questions:
                response = np.random.choice(response, num_questions, replace=False).tolist()

            return response
        
        except Exception as e:
            logger.error(f"Error generating initial questions for 2 Wheels: {e}")
            return []
    
    elif chat_option == "4 Wheels":
        return []
    elif chat_option == "Retail General":
        return []
    elif chat_option == "Retail Beauty":
        return []
    elif chat_option == "Retail FnB":
        return []
    elif chat_option == "Retail Drugstore":
        return []
