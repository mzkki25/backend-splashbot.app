from core.gemini import llm_code_gen, llm_analysis
from core.config import UPLOAD_DIR, LIVE
from core.minio import client as minio_client, MINIO_BUCKET
from core.logger import get_logger
from tools import search_web
from tools.csv_tool import load_dataset, get_dataset_info
from agents.macroeconomics_agent import build_macro_prompt, build_file_prompt
from agents.data_analysis_agent import build_code_prompt, build_business_prompt, execute_code_stage, build_fallback_prompt
from memory.chat_memory import get_conversation_context, save_turn
from prompt.follow_up_question_prompt import follow_up_question_gm, follow_up_question_ngm as fup_ngm_prompt_factory

from PIL import Image
from uuid import UUID

import ast
import google.generativeai as genai
import io
import os
import time
import datetime
import pandas as pd
import re

from sqlalchemy import select
from core.database import async_session
from models.file import File

from schemas.agent import AgentState

logger = get_logger(__name__)


async def run_agent(
    session_id: str,
    user_id: str,
    prompt: str,
    chat_option: str,
    file_id: str | None = None,
    file_url: str | None = None,
) -> dict:
    logger.info(f"Agent entry: session={session_id}, user={user_id}, option={chat_option}, file_id={file_id}")

    state = AgentState(
        session_id=session_id,
        user_id=user_id,
        prompt=prompt,
        chat_option=chat_option,
        file_id=file_id,
        file_url=file_url,
        references=None,
        response=None,
        follow_up_question=None,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        messages=[],
    )

    try:
        if chat_option == "General Macroeconomics":
            if file_id:
                result = await _handle_file(state)
            else:
                result = await _handle_web_search(state)
        else:
            result = await _handle_data_analysis(state)

        response_str = result["response"]
        if isinstance(response_str, dict):
            response_str = response_str.get("explanation", str(response_str))
        save_turn(session_id, prompt, response_str)

        logger.info(f"Agent completed: session={session_id}")
        return result
    except Exception:
        logger.error(f"Agent failed: session={session_id}, user={user_id}", exc_info=True)
        raise


async def _handle_web_search(state: AgentState) -> dict:
    logger.info(f"Web search started for session {state['session_id']}")
    search_results = search_web(state["prompt"], num_results=5)
    references = [r["link"] for r in search_results if r["link"]]
    snippets_formatted = "\n\n".join(
        f"**{r['title']}**\n{r['snippet']}\n[Link]({r['link']})"
        for r in search_results
    )

    context = get_conversation_context(state["session_id"])

    prompt_text = build_macro_prompt(context, state["prompt"], snippets_formatted)
    response = llm_analysis.invoke(prompt_text).content

    if "saya hanya dapat menjawab pertanyaan yang berkaitan dengan ekonomi" in response.lower():
        references = references or []

    follow_up_q = await _generate_follow_up_gm(state["prompt"], response)
    logger.info(f"Web search completed for session {state['session_id']}")

    return {
        "response": response,
        "file_url": None,
        "references": references,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
    }


async def _handle_file(state: AgentState) -> dict:
    logger.info(f"File processing started for session {state['session_id']}, file_id={state['file_id']}")

    async with async_session() as db:
        result = await db.execute(select(File).where(File.id == UUID(state["file_id"])))
        file_record = result.scalar_one_or_none()

    if not file_record:
        logger.warning(f"File not found: file_id={state['file_id']}")
        return {"response": "File not found", "file_url": None, "references": None, "follow_up_question": None, "created_at": state["created_at"]}

    object_key = file_record.storage_path
    content_type = file_record.content_type
    file_url = file_record.url

    logger.debug(f"File loaded: type={content_type}, key={object_key}")

    logger.debug(f"File loaded: type={content_type}, key={object_key}")

    context = get_conversation_context(state["session_id"])

    try:
        minio_resp = minio_client.get_object(MINIO_BUCKET, object_key)
        file_bytes = minio_resp.read()
        minio_resp.close()
        minio_resp.release_conn()
    except Exception as e:
        logger.error(f"Failed to read file from MinIO: {e}")
        return {"response": "Failed to read uploaded file", "file_url": None, "references": None, "follow_up_question": None, "created_at": state["created_at"]}

    if "application/pdf" in content_type:
        uploaded = genai.upload_file(
            path=io.BytesIO(file_bytes),
            display_name="PDF Document",
            mime_type="application/pdf",
        )
        while uploaded.state.name == "PROCESSING":
            time.sleep(1)
            uploaded = genai.get_file(uploaded.name)

        prompt_content = build_file_prompt(state["prompt"], uploaded, context)
        multimodal_model = genai.GenerativeModel("gemini-3-flash-preview")
        response = multimodal_model.generate_content(prompt_content).text
        time.sleep(0.5)
        genai.delete_file(uploaded.name)

    elif content_type.startswith("image/"):
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        prompt_content = build_file_prompt(state["prompt"], image, context)
        multimodal_model = genai.GenerativeModel("gemini-3-flash-preview")
        response = multimodal_model.generate_content(prompt_content).text

    else:
        response = "Unsupported file type"

    follow_up_q = await _generate_follow_up_gm(state["prompt"], response)
    logger.info(f"File processing completed for session {state['session_id']}")

    return {
        "response": response,
        "file_url": file_url,
        "references": None,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
    }


async def _handle_data_analysis(state: AgentState) -> dict:
    logger.info(f"Data analysis started for session {state['session_id']}, option={state['chat_option']}")
    chat_option = state["chat_option"]
    prompt = state["prompt"]

    context = get_conversation_context(state["session_id"])
    df = load_dataset(chat_option)

    code_prompt = build_code_prompt(chat_option, df, prompt, context)
    raw_code = llm_code_gen.invoke(code_prompt).content
    logger.debug(f"Code generation completed for session {state['session_id']}")

    cleaned_code = clean_code(raw_code)
    if LIVE == "development":
        logger.info(f"Generated code for session {state['session_id']}:\n{cleaned_code}")
    exec_result = execute_code_stage(chat_option, cleaned_code)

    if isinstance(exec_result, dict) and exec_result.get("type") == "error" and "Pertanyaan tidak dapat dijawab" in str(exec_result.get("message", "")):
        logger.info(f"Question unanswerable via data analysis for session {state['session_id']}")
        fallback_prompt = build_fallback_prompt(prompt, df)
        fb_response = llm_code_gen.invoke(fallback_prompt).content
        save_turn(state["session_id"], prompt, fb_response)
        return {
            "response": f"### Maaf, SPLASHBot Belum Dapat Menjawab :\n\n---\n{fb_response}",
            "file_url": None,
            "references": None,
            "follow_up_question": None,
            "created_at": state["created_at"],
        }

    business_prompt = build_business_prompt(chat_option, cleaned_code, exec_result, prompt, df, context)
    explanation = llm_analysis.invoke(business_prompt).content
    explanation = _clean_explanation(explanation)

    chart_result = _format_result(exec_result, state["user_id"])
    chart_json = None

    if chart_result and chart_result.strip().startswith("{"):
        chart_json = __import__("json").loads(chart_result)
        response_obj = {
            "explanation": f"### Ringkasan Temuan SPLASHBot:\n\n---\n{explanation}",
            "result": None,
        }
    elif chart_result:
        response_obj = f"### Ringkasan Temuan SPLASHBot:\n\n---\n{explanation}\n\n{chart_result}"
    else:
        response_obj = f"### Ringkasan Temuan SPLASHBot:\n\n---\n{explanation}"

    follow_up_q = await _generate_follow_up_ngm(prompt, explanation, chat_option)
    logger.info(f"Data analysis completed for session {state['session_id']}")

    return {
        "response": response_obj,
        "file_url": None,
        "references": None,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
        "chart_json": chart_json,
    }


def _format_result(exec_result, user_id: str) -> str | None:
    if isinstance(exec_result, dict):
        if exec_result.get("type") == "dataframe":
            df = pd.DataFrame(exec_result["data"])
            return df.head(20).to_markdown(index=False, tablefmt="github")
        elif exec_result.get("type") == "dict":
            data = exec_result["data"]
            if isinstance(data, dict) and "data" in data:
                return __import__("json").dumps(data)
            return __import__("json").dumps(data)
    return None


def clean_code(code: str) -> str:
    if "```python" in code:
        code = re.sub(r"(?s).*?```python\s*(.*?)\s*```.*", r"\1", code)
    elif "```" in code:
        code = re.sub(r"(?s).*?```\s*(.*?)\s*```.*", r"\1", code)
    code = code.replace("\r\n", "\n").strip()
    return code


def _clean_explanation(text: str) -> str:
    text = re.sub(r"^#*\s*Ringkasan Temuan SPLASHBot\s*:?\s*\n*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"^---+\s*\n*", "", text)
    return text.strip()


async def _generate_follow_up_gm(prompt: str, response: str) -> list[str] | None:
    prompt_text = follow_up_question_gm(prompt, response)
    raw = llm_code_gen.invoke(prompt_text).content.strip()
    raw = raw.replace("```python", "").replace("```", "").strip()
    try:
        result = ast.literal_eval(raw)
        if isinstance(result, list) and len(result) > 0:
            return result[:5]
    except Exception:
        pass
    lines = [q.strip(" \"'[]") for q in raw.split(",") if q.strip(" \"'[]")]
    return lines[:5] if lines else None


async def _generate_follow_up_ngm(prompt: str, response: str, chat_option: str) -> list[str] | None:
    df = load_dataset(chat_option)
    prompt_text = fup_ngm_prompt_factory(chat_option, df, prompt, response)
    raw = llm_code_gen.invoke(prompt_text).content.strip()
    raw = raw.replace("```python", "").replace("```", "").strip()
    try:
        result = ast.literal_eval(raw)
        if isinstance(result, list) and len(result) > 0:
            return result[:5]
    except Exception:
        pass
    lines = [q.strip(" \"'[]") for q in raw.split(",") if q.strip(" \"'[]")]
    return lines[:5] if lines else None
