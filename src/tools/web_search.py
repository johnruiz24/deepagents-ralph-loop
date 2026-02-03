"""Web search tools for the Research Agent using Tavily API."""

import os
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    url: str
    content: str
    score: float = 0.0
    source_type: str = "web"  # web, academic, official_docs, github


class WebSearchResults(BaseModel):
    """Collection of search results with metadata."""
    query: str
    results: list[SearchResult]
    total_results: int


def get_tavily_client() -> Optional["TavilyClient"]:
    """Get Tavily client if available."""
    if not TAVILY_AVAILABLE:
        return None
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None
    return TavilyClient(api_key=api_key)


def classify_source_type(url: str, title: str) -> str:
    """Classify the type of source based on URL and title."""
    url_lower = url.lower()
    title_lower = title.lower()

    # Official documentation
    if any(domain in url_lower for domain in [
        "docs.", ".readthedocs.", "documentation",
        "aws.amazon.com/", "cloud.google.com/", "azure.microsoft.com/",
        "langchain.com/docs", "python.org/doc"
    ]):
        return "official_docs"

    # GitHub repositories
    if "github.com" in url_lower:
        return "github"

    # Academic sources
    if any(domain in url_lower for domain in [
        "arxiv.org", "scholar.google", ".edu/", "ieee.org",
        "acm.org", "springer.com", "nature.com"
    ]):
        return "academic"

    # Technical blogs and trusted sources
    if any(domain in url_lower for domain in [
        "medium.com", "dev.to", "towardsdatascience.com",
        "blog.", "engineering."
    ]):
        return "technical_blog"

    return "web"


def score_source_credibility(source_type: str, url: str) -> float:
    """Score source credibility from 0.0 to 1.0."""
    base_scores = {
        "official_docs": 0.95,
        "github": 0.85,
        "academic": 0.90,
        "technical_blog": 0.70,
        "web": 0.50,
    }

    score = base_scores.get(source_type, 0.50)

    # Boost for known authoritative domains
    authoritative_domains = [
        "aws.amazon.com", "langchain.com", "python.org",
        "anthropic.com", "openai.com", "huggingface.co"
    ]
    if any(domain in url.lower() for domain in authoritative_domains):
        score = min(1.0, score + 0.10)

    return score


@tool
def web_search(query: str, max_results: int = 10) -> dict:
    """
    Search the web for information using Tavily API.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10)

    Returns:
        Dictionary with search results including titles, URLs, content snippets,
        source types, and credibility scores.
    """
    client = get_tavily_client()

    if not client:
        # Return mock results for testing when Tavily is not available
        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": "Tavily API not configured. Set TAVILY_API_KEY environment variable."
        }

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )

        results = []
        for item in response.get("results", []):
            source_type = classify_source_type(
                item.get("url", ""),
                item.get("title", "")
            )
            credibility = score_source_credibility(source_type, item.get("url", ""))

            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": credibility,
                "source_type": source_type,
            })

        # Sort by credibility score
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "answer": response.get("answer", ""),
        }

    except Exception as e:
        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "error": str(e),
        }


@tool
def search_official_docs(topic: str, technology: str) -> dict:
    """
    Search specifically for official documentation.

    Args:
        topic: The topic to search for
        technology: The technology/framework (e.g., 'langchain', 'aws bedrock')

    Returns:
        Dictionary with official documentation results.
    """
    # Build targeted query for official docs
    query = f"{topic} {technology} official documentation site:docs OR site:documentation"
    return web_search.invoke({"query": query, "max_results": 5})


@tool
def search_code_examples(topic: str, language: str = "python") -> dict:
    """
    Search for code examples on GitHub and documentation.

    Args:
        topic: The topic to search for
        language: Programming language (default: python)

    Returns:
        Dictionary with code example results.
    """
    query = f"{topic} {language} code example site:github.com OR site:docs"
    return web_search.invoke({"query": query, "max_results": 8})


# Export all tools as a list for easy registration
research_tools = [web_search, search_official_docs, search_code_examples]
