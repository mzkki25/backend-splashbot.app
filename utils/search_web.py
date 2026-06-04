from duckduckgo_search import DDGS


def search_web_snippets(user_query: str, num_results: int = 5) -> dict:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(user_query, max_results=num_results))

        titles = []
        links = []
        snippets_raw = []
        for r in results:
            titles.append(r["title"])
            links.append(r["href"])
            snippets_raw.append(r["body"])

        return {
            "list_title_results": titles,
            "list_linked_results": links,
            "list_snippet_results": snippets_raw,
            "snippet_results": "\n".join(snippets_raw),
        }
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return {
            "list_title_results": [],
            "list_linked_results": [],
            "list_snippet_results": [],
            "snippet_results": "",
        }
