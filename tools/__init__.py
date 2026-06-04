import json
import requests

from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ddgs import DDGS
from core.logger import get_logger

logger = get_logger(__name__)


class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the web")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Search the web using DuckDuckGo for economic and macroeconomic information. Returns titles, links, and snippets."
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, num_results: int = 5) -> str:
        result = search_web(query, num_results)
        return json.dumps(result, ensure_ascii=False)


def search_web(query: str, num_results: int = 5) -> list[dict]:
    logger.info(f"Web search: query='{query[:80]}...', num_results={num_results}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            logger.debug(f"DDGS returned {len(results)} results")
            
        return [{
            "title": r["title"], 
            "snippet": r["body"],
            "link": r["href"], 
        } for r in results]
    except Exception:
        logger.warning("DDGS search failed, falling back to DuckDuckGo API")

    try:
        url = "https://api.duckduckgo.com"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        resp = requests.get(url, params=params, timeout=10).json()
        results = []
        for topic in resp.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                    "link": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                })
        if results:
            return results
    except Exception:
        pass

    logger.warning("All search methods failed, returning fallback message")
    return [
        {
            "title": "Pencarian tidak tersedia",
            "link": "",
            "snippet": "Maaf, layanan pencarian web sedang tidak tersedia. Silakan coba lagi nanti.",
        }
    ]
