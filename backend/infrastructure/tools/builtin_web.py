"""Web search tools for agents.

Provides web search capability using a search API.
"""

import os
from langchain_core.tools import tool


def create_web_tools(tavily_api_key: str | None = None) -> list:
    """Create web search tools.

    Args:
        tavily_api_key: Tavily API key from settings (optional, falls back to env var)

    Returns:
        List of web-related tools
    """

    @tool
    def web_search(query: str, max_results: int = 5) -> str:
        """Search the internet for information.

        Use this to find current information, research topics, or answer
        questions that require up-to-date knowledge.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default 5)

        Returns:
            Search results with titles, snippets, and URLs
        """
        # Clamp max_results to safe range to prevent runaway API usage
        max_results = max(1, min(max_results, 10))

        # Check for Tavily API key (credential_store first, then env var)
        tavily_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        if tavily_key:
            return _tavily_search(query, max_results, tavily_key)

        # Check for SerpAPI key (fallback)
        serp_key = os.getenv("SERPAPI_KEY")
        if serp_key:
            return _serpapi_search(query, max_results, serp_key)

        # No API key configured - return helpful message
        return (
            "Web search is not configured. To enable web search:\n"
            "1. Go to Settings in the UI and add your Tavily API key, or\n"
            "2. Set TAVILY_API_KEY environment variable\n"
            "Get a key from: https://tavily.com"
        )

    return [web_search]


def _tavily_search(query: str, max_results: int, api_key: str) -> str:
    """Search using Tavily API."""
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(query, max_results=max_results)

        results = []
        for item in response.get("results", [])[:max_results]:
            results.append(
                f"**{item.get('title', 'No title')}**\n"
                f"{item.get('content', item.get('snippet', 'No description'))}\n"
                f"URL: {item.get('url', 'No URL')}"
            )

        if not results:
            return f"No results found for: {query}"

        return "\n\n---\n\n".join(results)

    except ImportError:
        return "Tavily package not installed. Run: pip install tavily-python"
    except Exception as e:
        return f"Search error: {str(e)}"


def _serpapi_search(query: str, max_results: int, api_key: str) -> str:
    """Search using SerpAPI."""
    try:
        import requests

        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": api_key,
                "num": max_results,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic_results", [])[:max_results]:
            results.append(
                f"**{item.get('title', 'No title')}**\n"
                f"{item.get('snippet', 'No description')}\n"
                f"URL: {item.get('link', 'No URL')}"
            )

        if not results:
            return f"No results found for: {query}"

        return "\n\n---\n\n".join(results)

    except ImportError:
        return "Requests package not installed. Run: pip install requests"
    except Exception as e:
        return f"Search error: {str(e)}"
