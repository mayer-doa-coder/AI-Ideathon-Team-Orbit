"""No real Tavily key in test/CI environments — these only cover the
graceful-degradation contract every caller (rag/qa.py, crop_recommendation,
season_planner) relies on: a missing key or failed request must never
crash the graph, just degrade to "the web had nothing either."
"""
import pytest

from app.core.config import settings
from app.tools import web_search as web_search_module
from app.tools.web_search import WebSearchError, web_search, web_search_as_docs


def test_web_search_raises_when_key_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "tavily_api_key", "")
    with pytest.raises(WebSearchError):
        web_search("fertilizer rate for jute")


def test_web_search_as_docs_degrades_to_empty_list_without_crashing(monkeypatch):
    monkeypatch.setattr(settings, "tavily_api_key", "")
    docs = web_search_as_docs("fertilizer rate for jute")
    assert docs == []


def test_web_search_as_docs_shape_matches_kb_docs(monkeypatch):
    # Same dict shape as retrieve_agri_knowledge's output is what lets web
    # results flow through the existing trace/sources pipeline unchanged.
    def fake_web_search(query, max_results=5):
        return [{"title": "Example result", "url": "https://example.com/a", "content": "some content"}]

    monkeypatch.setattr(web_search_module, "web_search", fake_web_search)
    docs = web_search_as_docs("anything")
    assert docs == [
        {
            "content": "some content",
            "crop": None,
            "topic": None,
            "section_heading": None,
            "page_number": None,
            "source_title": "Example result",
            "url": "https://example.com/a",
            "similarity": None,
        }
    ]
