from typing import Any
import pandas as pd
from prompt.macroeconomics_prompt import (
    macroeconomics_prompt_1,
    macroeconomics_prompt_2,
    fallback_response_prompt,
)
from tools.chart_tool import execute_analysis


def build_code_prompt(chat_option: str, df: pd.DataFrame, text: str, last_response: str | None) -> str:
    return macroeconomics_prompt_1(
        types=chat_option,
        df=df,
        text=text,
        last_response=last_response or "",
    )


def build_business_prompt(
    chat_option: str,
    generated_code: str,
    answer: Any,
    text: str,
    df: pd.DataFrame,
    last_response: str | None,
) -> str:
    return macroeconomics_prompt_2(
        types=chat_option,
        generated_code=generated_code,
        answer_the_code=answer,
        text=text,
        df=df,
        last_response=last_response or "",
    )


def execute_code_stage(chat_option: str, code: str) -> dict:
    import json
    result = execute_analysis(chat_option, code)
    return json.loads(result)


def build_fallback_prompt(text: str, df: pd.DataFrame) -> str:
    return fallback_response_prompt(text, df)
