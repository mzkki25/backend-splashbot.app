from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.gemini import llm_code_gen
from tools.csv_tool import load_dataset, get_dataset_info

router = APIRouter()


@router.get("")
async def init_question(chat_option: str) -> JSONResponse:
    try:
        if chat_option == "General Macroeconomics":
            initial_q = "Apa saja hal-hal utama yang dipelajari dalam ekonomi makro dan bagaimana pengaruhnya terhadap perekonomian suatu negara?"
            prompt = f"""Anda adalah SPLASHBot asisten AI ahli ekonomi. Buat hingga 5 pertanyaan awal singkat tentang ekonomi dalam format list Python.

Note: ini adalah initial question untuk user yang belum tahu apa yang harus ditanyakan.

Topik awal: "{initial_q}"

Tampilkan dalam format list Python:
["Pertanyaan 1?", "Pertanyaan 2?", ...]

Hanya list, tanpa penjelasan."""
            response = llm_code_gen.invoke(prompt).content
            response = response.replace("```python", "").replace("```", "").strip()
            import ast
            try:
                questions = ast.literal_eval(response)
            except Exception:
                questions = [q.strip('"\'').strip() for q in response.strip("[]").split(",") if q.strip()]
            init_questions = questions[:5]
        else:
            df = load_dataset(chat_option)
            info = get_dataset_info(chat_option)
            prompt = f"""Kamu adalah SPLASHBot AI Agent ahli ekonomi. Data tersedia:
- Jenis: {chat_option}
- Kolom: {info['columns']}
- Kota: {info['cities'][:10]}
- Provinsi: {info['provinces'][:5]}
- Tahun: {info['years']}

Buat hingga 5 pertanyaan awal singkat untuk user dalam format list Python:
["Pertanyaan 1?", "Pertanyaan 2?", ...]

Hanya list, tanpa penjelasan."""

            response = llm_code_gen.invoke(prompt).content
            response = response.replace("```python", "").replace("```", "").strip()
            import ast
            try:
                questions = ast.literal_eval(response)
            except Exception:
                questions = [q.strip('"\'').strip() for q in response.strip("[]").split(",") if q.strip()]
            init_questions = questions[:5]

        return JSONResponse(
            content={"init_questions": init_questions},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
