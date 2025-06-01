import pandas as pd
import uuid
import os
import time
import json

from core.firebase import bucket
from utils.preprocessing import clean_code, save_code, read_clean_python_file
from utils.prompt.macroeconomics_prompt import (
    fallback_response_prompt, macro_2wheels_prompt_1, macro_2wheels_prompt_2
)
from core.gemini import model, model_2

from core.logging_logger import setup_logger
logger = setup_logger(__name__)

def two_wheels_model(text, user_id, last_response):
    df = pd.read_csv('dataset/2_wheels.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        prompt = macro_2wheels_prompt_1(
            df=df, text=text,
            last_response=last_response if last_response else "",
        )

        generated_code = model.generate_content(contents=prompt).text
        generated_code = clean_code(generated_code)

        # save_code(generated_code, f"utils/_generated_code_{uid}.py")
        # generated_code = read_clean_python_file(filepath)

        logger.info(f"Generated code: {generated_code}")

        local_ns = {'df': df}
        exec(generated_code, {}, local_ns)
        answer_the_code = local_ns.get('final_answer') if 'final_answer' in local_ns else None

        time.sleep(0.03)

        prompt_2 = macro_2wheels_prompt_2(
            generated_code=generated_code, answer_the_code=answer_the_code,
            text=text, df=df, last_response=last_response if last_response else ""
        )

        explanation = model_2.generate_content(contents=prompt_2).text.replace("```python", "").replace("```", "").strip()

        formatted_result = ""
        if isinstance(answer_the_code, pd.DataFrame):
            formatted_result += answer_the_code.head(10).to_markdown(index=False, tablefmt="github")
        elif isinstance(answer_the_code, dict):
            blob = bucket.blob(f"users/{user_id}/{uuid.uuid4()}.json")

            json_string = json.dumps(answer_the_code)
            blob.upload_from_string(json_string, content_type="application/json")
            blob.make_public()

            formatted_result = blob.public_url
        else:
            formatted_result += ""

        return {
            "explanation": f"### Ringkasan Temuan SPLASHBot 🤖:\n\n---\n{explanation}",
            "result": formatted_result,
        }

    except Exception as e:
        logger.error(f"Error in two_wheels_model: {e}")

        fallback_response = model.generate_content(
            contents=fallback_response_prompt(text, df)
        ).text.replace("```python", "").replace("```", "").strip()

        return {
            "explanation": f"### Maaf, SPLASHBot Belum Dapat Menjawab 😢:\n\n---\n{fallback_response}",
            "result": None,
        }
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass
     
def four_wheels_model(text, user_id, last_response):
    answer = "Four wheels model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_general_model(text, user_id, last_response):
    answer = "Retail general model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_beauty_model(text, user_id, last_response):
    answer = "Retail beauty model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_fnb_model(text, user_id, last_response):
    answer = "Retail FnB model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }
    
def retail_drugstore_model(text, user_id, last_response):
    answer = "Retail drugstore model masih dalam tahap pengembangan dan belum tersedia untuk digunakan. Silakan coba lagi nanti."
    return {
        "explanation": answer,
        "result": None
    }