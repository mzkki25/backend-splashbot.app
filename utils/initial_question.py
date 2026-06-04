from core.gemini import llm_code_gen
from tools.csv_tool import load_dataset, get_dataset_info
from core.logger import get_logger

logger = get_logger(__name__)


def initial_questions_gm() -> list[str]:
    initial_q = "Apa saja hal-hal utama yang dipelajari dalam ekonomi makro?"
    prompt = f"""Anda adalah SPLASHBot AI ahli ekonomi. Buat 5 pertanyaan awal dalam format list Python tentang ekonomi makro.
    Contoh: ["Bagaimana data PDB dapat digunakan?", ...]
    Hanya list, tanpa penjelasan."""

    response = llm_code_gen.invoke(prompt).content
    response = response.replace("```python", "").replace("```", "").strip()
    import ast
    try:
        return ast.literal_eval(response)[:5]
    except Exception:
        lines = [q.strip('"\'').strip() for q in response.strip("[]").split(",") if q.strip()]
        return lines[:5]


def initial_questions_ngm(chat_option: str) -> list[str]:
    df = load_dataset(chat_option)
    info = get_dataset_info(chat_option)
    prompt = f"""Kamu SPLASHBot AI ahli ekonomi. Data: {chat_option}, kota={info['cities'][:10]}, tahun={info['years']}.
    Buat 5 pertanyaan awal bisnis dalam format list Python. Hanya list."""

    response = llm_code_gen.invoke(prompt).content
    response = response.replace("```python", "").replace("```", "").strip()
    import ast
    try:
        return ast.literal_eval(response)[:5]
    except Exception:
        return response.strip("[]").split('",')[ :5]
