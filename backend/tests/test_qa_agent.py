"""Unit tests for the qa_agent subagent's pure building blocks: the tool
factories' formatting logic and history construction. The tool-calling loop
itself (create_agent + a real LLM) isn't exercised here — that's an
integration concern, not a unit-testable pure function — but everything
that doesn't require a live LLM or network call is."""
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.nodes.qa_agent import (
    _build_history,
    _make_dashboard_tool,
    _trace_entry,
)


def test_trace_entry_shape():
    entry = _trace_entry("knowledge_base", {"query": "urea rate"}, "some content", "knowledge", "1 chunk retrieved")
    assert entry["type"] == "knowledge"
    assert entry["tool"] == "knowledge_base"
    assert entry["params"] == {"query": "urea rate"}
    assert "query='urea rate'" in entry["paramsDisplay"]
    assert entry["response"]["text"] == "some content"
    assert entry["summary"] == "1 chunk retrieved"


def test_trace_entry_truncates_long_response_text():
    entry = _trace_entry("web_search", {"query": "x"}, "a" * 5000, "knowledge", "summary")
    assert len(entry["response"]["text"]) == 2000


def test_build_history_excludes_current_message_and_keeps_last_turns():
    messages = [HumanMessage(content=f"msg {i}") for i in range(10)]
    state = {"messages": messages}
    history = _build_history(state)
    # last 6 turns before the final (current) message
    assert len(history) == 6
    assert history[-1].content == "msg 8"
    assert all(isinstance(m, HumanMessage) for m in history)


def test_build_history_empty_when_only_one_message():
    state = {"messages": [HumanMessage(content="only message")]}
    assert _build_history(state) == []


def test_dashboard_tool_reports_no_farm_when_nothing_set_up():
    trace: list[dict] = []
    tool_fn = _make_dashboard_tool({}, trace)
    result = tool_fn.invoke({})
    assert "No farm has been set up" in result
    assert trace[0]["tool"] == "farm_dashboard"


def test_dashboard_tool_includes_profile_crop_and_financials():
    trace: list[dict] = []
    state = {
        "farm_profile": {"location": "Khulna", "acres": 2.0, "lat": 22.8, "lon": 89.5},
        "selected_crop": "Mungbean",
        "season_plan": {
            "sowing_window": {"start": "2026-08-01", "end": "2026-08-05"},
            "harvest_window": {"start": "2026-10-01", "end": "2026-10-10"},
            "fertilizer_schedule": [
                {"name": "Urea", "amount_kg_per_acre": 30, "date": "2026-08-01", "status": "pending"}
            ],
        },
        "financials": {
            "items": [{"label": "Seeds", "amount": 2430}],
            "cost": 25430,
            "revenue": 47430,
            "profit": 22000,
            "roi": 87,
            "breakEvenTons": 0.3,
        },
    }
    tool_fn = _make_dashboard_tool(state, trace)
    result = tool_fn.invoke({})

    assert "location=Khulna" in result
    assert "lat=" not in result  # lat/lon excluded from the profile line
    assert "Selected crop: Mungbean" in result
    assert "Sowing window: 2026-08-01 to 2026-08-05" in result
    assert "Financial breakdown" in result
    assert "৳25,430" in result
    assert trace[0]["summary"] == "read farmer's own dashboard data"


def test_dashboard_tool_has_no_required_args():
    # Must be callable with an empty input — the model shouldn't need to
    # invent arguments just to look up the farmer's own dashboard.
    tool_fn = _make_dashboard_tool({"location": "Khulna"}, [])
    assert tool_fn.invoke({}) is not None
