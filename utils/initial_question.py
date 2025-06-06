from core.gemini import model
from helper.prompt.initial_question_prompt import (
    init_question_gm, init_question_ngm
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

        prompt = init_question_gm(initial_question)
        response = eval(model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip())

        num_questions = np.random.randint(3, 6)
        if len(response) > num_questions:
            response = np.random.choice(response, num_questions, replace=False).tolist()

        return response

def initial_questions_ngm(chat_option):
    try:
        if chat_option == "2 Wheels":
            df = pd.read_csv('helper/dataset/2_wheels.csv')
        elif chat_option == "4 Wheels":
            df = pd.read_csv('helper/dataset/4_wheels.csv')
        elif chat_option == "Retail General":
            df = pd.read_csv('helper/dataset/retail.csv')
        elif chat_option == "Retail Beauty":
            df = pd.read_csv('helper/dataset/beauty.csv')
        elif chat_option == "Retail FnB":
            df = pd.read_csv('helper/dataset/fnb.csv')
        elif chat_option == "Retail Drugstore":
            df = pd.read_csv('helper/dataset/drugstore.csv')

        prompt = init_question_ngm(chat_option, df)

        response = eval(model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip())
        num_questions = np.random.randint(3, 6)

        if len(response) > num_questions:
            response = np.random.choice(response, num_questions, replace=False).tolist()

        return response
    
    except Exception as e:
        logger.error(f"Error generating initial questions for {chat_option}: {e}")
        return []
