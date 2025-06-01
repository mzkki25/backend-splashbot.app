import requests
import random

from core.config import GCS_API_KEY, GCS_CX

def search_web_snippets(user_query, num_results=8):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GCS_API_KEY,
            "cx": GCS_CX,
            "q": user_query,
            "num": random.randint(4, num_results),
        }
        
        response = requests.get(url, params=params).json()
        results = []
        
        for item in response.get("items", []):
            title   = item.get("title", "No Title")
            link    = item.get("link", "")
            snippet = item.get("snippet", "")

            results.append({
                "title": title, 
                "link": link, 
                "snippet": snippet
            })
        
        title_results   = []
        linked_results  = []
        snippet_results = []

        for linked_result in results:
            title_results.append(linked_result["title"])
            linked_results.append(linked_result["link"])
            snippet_results.append(linked_result["snippet"])

        return {
            "list_title_results"    : title_results,
            "list_linked_results"   : linked_results,
            "list_snippet_results"  : snippet_results,
            "snippet_results"       : "\n".join(snippet_results),
        }
    
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return []