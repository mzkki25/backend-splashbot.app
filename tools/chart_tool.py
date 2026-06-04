from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

import json
import uuid
import os
import pandas as pd
import plotly.io as pio

from schemas.agent import DataAnalysisInput
from plotly.utils import PlotlyJSONEncoder

from tools.csv_tool import load_dataset
from core.logger import get_logger

logger = get_logger(__name__)


class DataAnalysisTool(BaseTool):
    name: str = "data_analysis"
    description: str = "Execute Python code to analyze CSV datasets. Use pandas for data manipulation, plotly for charts. Output goes to 'final_answer' variable."
    args_schema: Type[BaseModel] = DataAnalysisInput

    def _run(self, chat_option: str, code: str) -> str:
        return execute_analysis(chat_option, code)


def execute_analysis(chat_option: str, code: str) -> str:
    logger.info(f"Executing analysis: option={chat_option}")
    logger.debug(f"Analysis code:\n{code}")
    df = load_dataset(chat_option)
    local_ns: dict = {"df": df, "pd": pd, "json": json, "PlotlyJSONEncoder": PlotlyJSONEncoder}
    try:
        exec(code, {}, local_ns)
        result = local_ns.get("final_answer")
        if result is None:
            logger.warning(f"No final_answer variable set for option={chat_option}")
            return json.dumps({"type": "error", "message": "No final_answer variable set"})
        if isinstance(result, pd.DataFrame):
            logger.debug(f"Analysis result: DataFrame with {result.shape[0]} rows")
            return json.dumps({"type": "dataframe", "data": result.head(50).to_dict(orient="records"), "columns": result.columns.tolist()})
        if isinstance(result, dict):
            return json.dumps({"type": "dict", "data": result}, cls=PlotlyJSONEncoder)
        return json.dumps({"type": "text", "data": str(result)})
    except Exception as e:
        logger.error(f"Analysis execution error for option={chat_option}: {e}", exc_info=True)
        return json.dumps({"type": "error", "message": str(e)})
