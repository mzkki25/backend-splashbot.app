from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from core.gemini import llm_code_gen
from core.logger import get_logger
from tools.csv_tool import load_dataset
from prompt.initial_question_prompt import init_question_gm, init_question_ngm

logger = get_logger(__name__)

router = APIRouter()


@router.get("")
async def init_question(chat_option: str) -> JSONResponse:
    try:
        logger.info(f"Initial question request, chat_option={chat_option}")

        if chat_option == "General Macroeconomics":
            initial_q = "Apa saja hal-hal utama yang dipelajari dalam ekonomi makro dan bagaimana pengaruhnya terhadap perekonomian suatu negara?"
            prompt = init_question_gm(initial_q)
            raw = llm_code_gen.invoke(prompt).content
        else:
            df = load_dataset(chat_option)
            prompt = init_question_ngm(chat_option, df)
            raw = llm_code_gen.invoke(prompt).content

        raw = raw.replace("```python", "").replace("```", "").strip()
        import ast
        try:
            questions = ast.literal_eval(raw)
            if not isinstance(questions, list):
                questions = []
        except Exception:
            questions = [q.strip('"\'').strip() for q in raw.strip("[]").split(",") if q.strip()]

        import numpy as np
        num = np.random.randint(3, 6)
        if len(questions) > num:
            questions = np.random.choice(questions, num, replace=False).tolist()

        logger.info(f"Generated {len(questions)} initial questions for {chat_option}")
        return JSONResponse(
            content={"init_questions": questions[:5]},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error(f"Error generating initial questions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
