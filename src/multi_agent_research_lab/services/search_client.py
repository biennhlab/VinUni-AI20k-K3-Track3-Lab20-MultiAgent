"""Search client abstraction for ResearcherAgent."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import SourceDocument


from multi_agent_research_lab.core.config import get_settings

class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        settings = get_settings()
        api_key = settings.tavily_api_key
        
        if not api_key:
            # Fallback mock search for demonstration
            return [
                SourceDocument(
                    title="Mock Document 1",
                    url="https://example.com/mock1",
                    snippet=f"This is a mock search result for query: {query}. It contains some relevant information.",
                ),
                SourceDocument(
                    title="Mock Document 2",
                    url="https://example.com/mock2",
                    snippet=f"Another mock result discussing {query} in detail.",
                )
            ]
            
        # Call Tavily API
        import requests
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SourceDocument(
                    title=item.get("title", "No Title"),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")
                ))
            return results
        except Exception as e:
            raise RuntimeError(f"Search API failed: {str(e)}") from e
