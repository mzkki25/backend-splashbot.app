from langchain_core.tools import tool
import pandas as pd
import os

from core.logger import get_logger

logger = get_logger(__name__)

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "helper", "dataset")

DATASET_MAP: dict[str, str] = {
    "2 Wheels": "2_wheels.csv",
    "4 Wheels": "4_wheels.csv",
    "Retail General": "retail.csv",
    "Retail Beauty": "beauty.csv",
    "Retail FnB": "fnb.csv",
    "Retail Drugstore": "drugstore.csv",
}


def load_dataset(chat_option: str) -> pd.DataFrame:
    filename = DATASET_MAP.get(chat_option)
    if not filename:
        logger.error(f"Unknown chat option: {chat_option}")
        raise ValueError(f"Unknown chat option: {chat_option}")
    path = os.path.join(DATASET_DIR, filename)
    df = pd.read_csv(path)
    df = df.fillna(0)
    logger.debug(f"Loaded dataset '{chat_option}' from {filename}: {len(df)} rows, {len(df.columns)} columns")
    return df


def get_dataset_info(chat_option: str) -> dict:
    df = load_dataset(chat_option)
    info = {
        "chat_option": chat_option,
        "columns": df.columns.tolist(),
        "provinces": df["prov"].unique().tolist() if "prov" in df.columns else [],
        "cities": df["kab"].unique().tolist() if "kab" in df.columns else [],
        "years": sorted(df["year"].unique().tolist()) if "year" in df.columns else [],
        "row_count": len(df),
    }
    logger.debug(f"Dataset info for '{chat_option}': {info['row_count']} rows")
    return info
