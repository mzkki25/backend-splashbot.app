import json
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from duckduckgo_search import DDGS


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
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        return [{"title": r["title"], "link": r["href"], "snippet": r["body"]} for r in results]
    except Exception as e:
        return [{"title": "Search error", "link": "", "snippet": str(e)}]
