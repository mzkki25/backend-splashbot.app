from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from core.gemini import llm_code_gen, llm_analysis
from core.config import UPLOAD_DIR
from tools import search_web
from tools.csv_tool import load_dataset, get_dataset_info
from agents.macroeconomics_agent import build_macro_prompt, build_file_prompt
from agents.data_analysis_agent import build_code_prompt, build_business_prompt, execute_code_stage, build_fallback_prompt
from memory.chat_memory import get_message_history, set_agent_memory, get_agent_memory

from PIL import Image

import uuid
import google.generativeai as genai
import io
import os
import time
import datetime

from sqlalchemy import select
from core.database import async_session
from models.file import File

from schemas.agent import AgentState



async def run_agent(
    session_id: str,
    user_id: str,
    prompt: str,
    chat_option: str,
    file_id: str | None = None,
    file_url: str | None = None,
) -> dict:
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

    if chat_option == "General Macroeconomics":
        if file_id:
            result = await _handle_file(state)
        else:
            result = await _handle_web_search(state)
    else:
        result = await _handle_data_analysis(state)

    return result


async def _handle_web_search(state: AgentState) -> dict:
    search_results = search_web(state["prompt"], num_results=5)
    references = [r["link"] for r in search_results if r["link"]]
    snippets_formatted = "\n\n".join(
        f"**{r['title']}**\n{r['snippet']}\n[Link]({r['link']})"
        for r in search_results
    )

    last_response = get_agent_memory(state["session_id"], "last_response")

    prompt_text = build_macro_prompt(last_response, state["prompt"], snippets_formatted)
    response = llm_analysis.invoke(prompt_text).content

    if "saya hanya dapat menjawab pertanyaan yang berkaitan dengan ekonomi" in response:
        references = None
    if "splash" in response.lower():
        references = None

    follow_up_q = await _generate_follow_up_gm(state["prompt"], response)

    set_agent_memory(state["session_id"], "last_response", response)

    return {
        "response": response,
        "file_url": None,
        "references": references,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
    }


async def _handle_file(state: AgentState) -> dict:
    async with async_session() as db:
        from uuid import UUID
        result = await db.execute(select(File).where(File.id == UUID(state["file_id"])))
        file_record = result.scalar_one_or_none()

    if not file_record:
        return {"response": "File not found", "file_url": None, "references": None, "follow_up_question": None, "created_at": state["created_at"]}

    file_path = file_record.storage_path
    content_type = file_record.content_type
    file_url = file_record.url

    full_path = os.path.join(UPLOAD_DIR, os.path.relpath(file_path, UPLOAD_DIR + "/"))
    if not os.path.exists(full_path):
        full_path = file_path

    last_response = get_agent_memory(state["session_id"], "last_response")

    if "application/pdf" in content_type:
        with open(full_path, "rb") as f:
            pdf_bytes = f.read()
        uploaded = genai.upload_file(
            path=io.BytesIO(pdf_bytes),
            display_name="PDF Document",
            mime_type="application/pdf",
        )
        while uploaded.state.name == "PROCESSING":
            time.sleep(1)
            uploaded = genai.get_file(uploaded.name)

        prompt_content = build_file_prompt(state["prompt"], uploaded, last_response)
        multimodal_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = multimodal_model.generate_content(prompt_content).text
        time.sleep(0.5)
        genai.delete_file(uploaded.name)

    elif content_type.startswith("image/"):
        image = Image.open(full_path).convert("RGB")
        prompt_content = build_file_prompt(state["prompt"], image, last_response)
        multimodal_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = multimodal_model.generate_content(prompt_content).text

    else:
        response = "Unsupported file type"

    follow_up_q = await _generate_follow_up_gm(state["prompt"], response)
    set_agent_memory(state["session_id"], "last_response", response)

    return {
        "response": response,
        "file_url": file_url,
        "references": None,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
    }


async def _handle_data_analysis(state: AgentState) -> dict:
    chat_option = state["chat_option"]
    prompt = state["prompt"]

    last_response = get_agent_memory(state["session_id"], "last_response")
    df = load_dataset(chat_option)

    code_prompt = build_code_prompt(chat_option, df, prompt, last_response)
    raw_code = llm_code_gen.invoke(code_prompt).content

    cleaned_code = clean_code(raw_code)
    exec_result = execute_code_stage(chat_option, cleaned_code)

    if isinstance(exec_result, dict) and exec_result.get("type") == "error" and "Pertanyaan tidak dapat dijawab" in str(exec_result.get("message", "")):
        fallback_prompt = build_fallback_prompt(prompt, df)
        fb_response = llm_code_gen.invoke(fallback_prompt).content
        set_agent_memory(state["session_id"], "last_response", fb_response)
        return {
            "response": f"### Maaf, SPLASHBot Belum Dapat Menjawab :\n\n---\n{fb_response}",
            "file_url": None,
            "references": None,
            "follow_up_question": None,
            "created_at": state["created_at"],
        }

    business_prompt = build_business_prompt(chat_option, cleaned_code, exec_result, prompt, df, last_response)
    explanation = llm_analysis.invoke(business_prompt).content

    formatted_result = _format_result(exec_result, state["user_id"])

    full_response = f"### Ringkasan Temuan SPLASHBot:\n\n---\n{explanation}"
    if formatted_result:
        full_response += f"\n\n{formatted_result}"

    follow_up_q = await _generate_follow_up_ngm(prompt, explanation, chat_option)
    set_agent_memory(state["session_id"], "last_response", explanation)

    return {
        "response": full_response,
        "file_url": None,
        "references": None,
        "follow_up_question": follow_up_q,
        "created_at": state["created_at"],
    }


def _format_result(exec_result, user_id: str) -> str | None:
    if isinstance(exec_result, dict):
        if exec_result.get("type") == "dataframe":
            import pandas as pd
            df = pd.DataFrame(exec_result["data"])
            return df.head(20).to_markdown(index=False, tablefmt="github")
        elif exec_result.get("type") == "dict":
            json_str = __import__("json").dumps(exec_result["data"])
            os.makedirs(os.path.join(UPLOAD_DIR, str(user_id)), exist_ok=True)
            uid = str(uuid.uuid4() if "uuid" in dir() else __import__("uuid").uuid4())
            json_path = os.path.join(UPLOAD_DIR, str(user_id), f"{uid}.json")
            with open(json_path, "w") as f:
                f.write(json_str)
            return json_path
    return None


def clean_code(code: str) -> str:
    import re
    if "```python" in code:
        code = re.sub(r"(?s).*?```python\s*(.*?)\s*```.*", r"\1", code)
    elif "```" in code:
        code = re.sub(r"(?s).*?```\s*(.*?)\s*```.*", r"\1", code)
    code = code.replace("\r\n", "\n").strip()
    return code


async def _generate_follow_up_gm(prompt: str, response: str) -> list[str] | None:
    fup_prompt = f"""Kamu adalah SPLASHBot. Buatlah hingga 3 pertanyaan lanjutan singkat tentang ekonomi berdasarkan:
Pertanyaan user: "{prompt}"
Jawaban singkat: "{response[:500]}"

Format: list Python, contoh: ["Pertanyaan 1?", "Pertanyaan 2?"]
Hanya list, tanpa penjelasan."""

    raw = llm_code_gen.invoke(fup_prompt).content.strip()
    raw = raw.replace("```python", "").replace("```", "").strip()
    try:
        import ast
        result = ast.literal_eval(raw)
        if isinstance(result, list) and len(result) > 0:
            return result[:3]
    except Exception:
        pass
    lines = [q.strip(" \"'[]") for q in raw.split(",") if q.strip(" \"'[]")]
    return lines[:3] if lines else None


async def _generate_follow_up_ngm(prompt: str, response: str, chat_option: str) -> list[str] | None:
    info = get_dataset_info(chat_option)
    fup_prompt = f"""Kamu adalah SPLASHBot. Buatlah hingga 3 pertanyaan lanjutan singkat tentang data {chat_option} berdasarkan:
Pertanyaan user: "{prompt}"
Jawaban singkat: "{response[:500]}"
Kota tersedia: {info['cities'][:10]}
Tahun tersedia: {info['years']}

Format: list Python, contoh: ["Pertanyaan 1?", "Pertanyaan 2?"]
Hanya list, tanpa penjelasan."""

    raw = llm_code_gen.invoke(fup_prompt).content.strip()
    raw = raw.replace("```python", "").replace("```", "").strip()
    try:
        import ast
        result = ast.literal_eval(raw)
        if isinstance(result, list) and len(result) > 0:
            return result[:3]
    except Exception:
        pass
    lines = [q.strip(" \"'[]") for q in raw.split(",") if q.strip(" \"'[]")]
    return lines[:3] if lines else None
