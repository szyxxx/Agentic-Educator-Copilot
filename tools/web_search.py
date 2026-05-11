"""
Educator Copilot — Web Search Tool
====================================
Searches for academic references via DuckDuckGo.
"""

from langchain_core.tools import tool


@tool
def web_search_tool(query: str, max_results: int = 3) -> list[dict]:
    """
    Mencari referensi pustaka atau sumber belajar tambahan yang relevan.
    Digunakan saat agent perlu menyarankan referensi untuk topik tertentu dalam RPS.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query + " academic reference textbook",
                max_results=max_results,
            ))
        return [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results
        ]
    except ImportError:
        return [{"title": "DuckDuckGo search unavailable",
                 "url": "", "snippet": "Install: pip install duckduckgo-search"}]
    except Exception as e:
        return [{"title": "Search failed", "url": "", "snippet": str(e)}]
