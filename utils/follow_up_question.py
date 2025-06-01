from core.gemini import model
from utils.preprocessing import clean_python_list
from utils.prompt.follow_up_question_prompt import (
    follow_up_question_gm, follow_up_question_2wheels
)


import numpy as np
import pandas as pd

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

def recommend_follow_up_questions_gm(prompt, response, file_id_input=None):
    try:
        if file_id_input:
            return []
        else:
            prompt = follow_up_question_gm(prompt, response)

            response_list = model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip()
            logger.info(f"Response recommend_follow_up_questions_gm: {response_list}")
            
            try:
                response_list_eval = eval(clean_python_list(response_list))
            except Exception as e:
                response_list_eval = clean_python_list(response_list)

            num_questions = np.random.randint(3, 6)

            if len(response_list_eval) > num_questions:
                response_list_eval = np.random.choice(response_list_eval, num_questions, replace=False).tolist()

            return response_list_eval
        
    except Exception as e:
        logger.info(f"Response: {response}")
        logger.error(f"Error generating follow-up questions General Macroeconomics: {e}")
        return []
    
def recommend_follow_up_questions_ngm(prompt, response, chat_option):
    if chat_option == "2 Wheels":
        try:
            df = pd.read_csv('dataset/2_wheels.csv')

            prompt = follow_up_question_2wheels(df, prompt, response)

            response_list = model.generate_content(contents=prompt).text.replace("```python", "").replace("```", "").strip()
            logger.info(f"Response recommend_follow_up_questions_ngm: {response_list}")

            try:
                response_list_eval = eval(clean_python_list(response_list))
            except Exception as e:
                response_list_eval = clean_python_list(response_list)

            num_questions = np.random.randint(3, 6)

            if len(response_list_eval) > num_questions:
                response_list_eval = np.random.choice(response_list_eval, num_questions, replace=False).tolist()

            return response_list_eval
        
        except Exception as e:
            logger.error(f"Response: {response_list}")
            logger.error(f"Error generating follow-up questions for 2 Wheels: {e}")
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