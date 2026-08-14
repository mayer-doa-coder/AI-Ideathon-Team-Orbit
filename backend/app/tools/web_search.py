"""Web search fallback for when the local knowledge base has nothing
relevant for a query — real Tavily API results with real URLs, not an
invented answer. This is deliberately only ever a fallback: every caller
in `nodes/` tries `retrieve_agri_knowledge` first and only reaches here
when that came back with zero chunks, so the knowledge-base+RAG path stays
the primary grounding story and web results are always clearly labeled as
such (title prefixed, a real `url` present) wherever they surface — trace
log, sources panel, generated answer.
"""
import time

import httpx

from app.core.config import settings

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT = 15.0
CACHE_TTL_SECONDS = 1800

_cache: dict[str, tuple[float, list[dict]]] = {}


class WebSearchError(Exception):
    """Raised when Tavily isn't configured, can't be reached, or returns nothing usable."""


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Returns [{title, url, content}], most relevant first. Raises
    WebSearchError on any failure — callers decide how to degrade (see
    `web_search_as_docs`, which swallows this and returns an empty list)."""
    key = f"{query.strip().lower()}::{max_results}"
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    if not settings.tavily_api_key:
        raise WebSearchError("TAVILY_API_KEY is not configured — web search fallback is unavailable.")

    try:
        response = httpx.post(
            TAVILY_SEARCH_URL,
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise WebSearchError(f"Web search request failed for '{query}': {exc}") from exc

    results = [
        {
            "title": r.get("title") or r.get("url", ""),
            "url": r.get("url", ""),
            "content": (r.get("content") or "")[:1500],
        }
        for r in (payload.get("results") or [])
        if r.get("url")
    ]
    _cache[key] = (time.monotonic(), results)
    return results


def web_search_as_docs(query: str, max_results: int = 5) -> list[dict]:
    """Wraps `web_search` results in the same dict shape
    `retrieve_agri_knowledge` returns (`content`, `source_title`, ...), so
    every caller can feed web results through the exact same trace_log /
    retrieved_docs / sources-panel pipeline already built for KB chunks —
    no separate state field needed. `url` (never present on a KB doc) is
    what the frontend uses to render a real clickable link instead of a
    page-number citation. Never raises — a missing key or a failed request
    degrades to an empty list, same as "the web had nothing either."
    """
    try:
        results = web_search(query, max_results=max_results)
    except WebSearchError:
        return []

    return [
        {
            "content": r["content"],
            "crop": None,
            "topic": None,
            "section_heading": None,
            "page_number": None,
            "source_title": r["title"],
            "url": r["url"],
            "similarity": None,
        }
        for r in results
    ]
