import pandas as pd
import uuid
import os
import time
import json

from core.firebase import bucket
from utils.prompt.macroeconomics_prompt import (
    fallback_response_prompt, macroeconomics_prompt_1, macroeconomics_prompt_2
)
from core.gemini import model, model_2
from utils.preprocessing import clean_code

from core.logging_logger import setup_logger
logger = setup_logger(__name__)


def handle_macroeconomics_model(
    types: str,
    df: pd.DataFrame, text: str, user_id: str, last_response: str = None
):
    prompt = macroeconomics_prompt_1(
        types=types, df=df, text=text,
        last_response=last_response if last_response else "",
    )

    generated_code = model.generate_content(contents=prompt).text
    generated_code = clean_code(generated_code)

    logger.info(f"Generated code: {generated_code}")

    local_ns = {'df': df}
    exec(generated_code, {}, local_ns)
    answer_the_code = local_ns.get('final_answer') if 'final_answer' in local_ns else None

    prompt_2 = macroeconomics_prompt_2(
        types=types, generated_code=generated_code, answer_the_code=answer_the_code,
        text=text, df=df, last_response=last_response if last_response else ""
    )

    explanation = model_2.generate_content(
        contents=prompt_2
    ).text.replace("```python", "").replace("```", "").strip()

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

def handle_fallback_response(text, df, e):
    logger.error(f"Error in two_wheels_model: {e}")

    fallback_response = model.generate_content(
        contents=fallback_response_prompt(text, df)
    ).text.replace("```python", "").replace("```", "").strip()

    return {
        "explanation": f"### Maaf, SPLASHBot Belum Dapat Menjawab 😢:\n\n---\n{fallback_response}",
        "result": None,
    }

# ===== Model Functions ===== #

def two_wheels_model(text, user_id, last_response):
    df = pd.read_csv('dataset/2_wheels.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="2 Wheels",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res

    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

def four_wheels_model(text, user_id, last_response):
    df = pd.read_csv('dataset/4_wheels.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="4 Wheels",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res
    
    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

def retail_general_model(text, user_id, last_response):
    df = pd.read_csv('dataset/retail.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="Retail General",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res
    
    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

def retail_beauty_model(text, user_id, last_response):
    df = pd.read_csv('dataset/beauty.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="Retail Beauty",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res
    
    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

def retail_fnb_model(text, user_id, last_response):
    df = pd.read_csv('dataset/fnb.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="Retail FnB",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res
    
    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass

def retail_drugstore_model(text, user_id, last_response):
    df = pd.read_csv('dataset/drugstore.csv')
    uid = str(uuid.uuid4())
    filepath = f"utils/_generated_code_{uid}.py"

    try:
        res = handle_macroeconomics_model(
            types="Retail Drugstore",
            df=df, text=text, user_id=user_id, last_response=last_response
        )
        return res
    
    except Exception as e:
        return handle_fallback_response(text, df, e)
    
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass