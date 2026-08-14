"""General QA subagent — the one genuinely agentic node in this graph.

Every other node calls its tool(s) unconditionally because the tool call
IS the node's job (`weather_tool` always fetches weather, `season_planner`
always retrieves grounded docs before writing a plan). A farmer's open-ended
question is different: it might need their own dashboard data (crop, plan,
financial breakdown), grounded knowledge-base material, a live weather
forecast, a web search, some combination, or none of those — and which
applies isn't knowable until the model reads the question. So this node
hands a fixed toolbox to a `create_agent` (langchain, v1) tool-calling loop
and lets the model decide which tools to call and in what order, instead of
this file hardcoding one fixed retrieval path for every question the way
the old single-shot `general_qa` node did.

The "no invented data" and trace-verifiability guarantees the rest of the
graph relies on still hold: every tool is a thin wrapper around the same
deterministic functions every other node already uses
(`retrieve_agri_knowledge`, `web_search_as_docs`, `geocode_location`/
`get_weather_forecast`), each tool call appends one real entry to a shared
`trace` list as a direct side effect of running (not reconstructed after
the fact from the LLM's account of what it did), and any KB/web doc a tool
actually retrieves lands in `retrieved_docs` the same way it does from
`general_qa`'s old single retrieval call. The model only decides *whether*
and *when* to call a tool — never what the tool returns.
"""
from typing import Callable

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.core.config import settings
from app.db.session import SessionLocal
from app.tools.rag import is_grounded_enough, retrieve_agri_knowledge
from app.tools.weather import geocode_location, get_weather_forecast
from app.tools.web_search import web_search_as_docs

try:
    from langchain.tools import tool
except ImportError:  # pragma: no cover - fallback for older langchain layouts
    from langchain_core.tools import tool

HISTORY_TURNS = 6

SYSTEM_PROMPT = (
    "You are Green Leaf AI, an agricultural advisor for farmers in Bangladesh, talking "
    "directly to one specific farmer about their specific farm. You have four tools: "
    "farm_dashboard (the farmer's own farm profile, selected crop, season plan, and "
    "financial cost/revenue/profit breakdown, exactly as already shown on their "
    "dashboard), knowledge_base (grounded agronomic reference material — fertilizer "
    "rates, irrigation timing, pest and disease control, planting technique), "
    "current_weather (a live forecast for the farmer's farm or another named place), and "
    "web_search (general web results). "
    "Decide which tools the question actually needs — don't call ones that aren't "
    "relevant, and never state a fact one of these tools could answer for certain (their "
    "crop, dates, costs, budget, or current weather) from memory or a guess. This applies "
    "to ANY fact you are not personally, permanently certain of from general farming "
    "knowledge — current or recent conditions, prices, statistics, or anything about a "
    "specific named place: always call knowledge_base and/or web_search before answering, "
    "even if you believe you already know the answer. Never answer from your own general "
    "knowledge just because a tool call feels unnecessary — an ungrounded answer that "
    "happens to be right is still a failure here, because nothing backs it up in the trace. "
    "If the question refers to 'the plan', 'the dashboard', 'the budget', 'my crop', "
    "'the breakdown', or anything else already tracked for this farmer, call "
    "farm_dashboard first — that data is real and already computed. For general "
    "agronomic how-to questions, call knowledge_base. For anything about current or "
    "upcoming weather, call current_weather — never answer a weather question from "
    "memory. Only call web_search when knowledge_base comes back empty or clearly "
    "irrelevant, or the question needs something a farming reference wouldn't have. "
    "Answer in plain prose formatted for a plain-text chat bubble — no markdown, no "
    "asterisks, no headers, no bullet or numbered list syntax. Be concise and practical. "
    "If you still can't answer after checking the relevant tools, say so plainly instead "
    "of guessing."
)


def _trace_entry(tool_name: str, params: dict, response_text: str, entry_type: str, summary: str) -> dict:
    params_display = ", ".join(f"{k}={v!r}" for k, v in params.items() if v is not None) or "()"
    return {
        "type": entry_type,
        "tool": tool_name,
        "paramsDisplay": params_display,
        "params": params,
        "response": {"text": response_text[:2000]},
        "summary": summary,
    }


def _build_history(state: AgentState) -> list:
    messages = state.get("messages") or []
    recent = messages[-(HISTORY_TURNS + 1):-1] if len(messages) > 1 else []
    history = []
    for m in recent:
        if isinstance(m, HumanMessage) and m.content:
            history.append(HumanMessage(content=m.content))
        elif isinstance(m, AIMessage) and m.content:
            history.append(AIMessage(content=m.content))
    return history


def _make_dashboard_tool(state: AgentState, trace: list[dict]) -> Callable:
    profile = state.get("farm_profile") or {}
    crop = state.get("selected_crop")
    plan = state.get("season_plan") or {}
    financials = state.get("financials") or {}

    @tool
    def farm_dashboard() -> str:
        """Look up the farmer's own dashboard: farm profile (location, acres,
        soil type, water availability, budget, season), selected crop, season
        plan (sowing/harvest windows, fertilizer schedule, irrigation
        schedule, pest/disease watch), and the financial cost/revenue/profit
        breakdown already computed for their plan. Use this for any question
        about THEIR farm, plan, budget, or numbers already on their
        dashboard — not for general agricultural questions."""
        if not profile and not crop:
            text = "No farm has been set up yet — there's nothing on the dashboard."
            trace.append(_trace_entry("farm_dashboard", {}, text, "dashboard", "no farm set up yet"))
            return text

        lines = []
        if profile:
            parts = [f"{k}={v}" for k, v in profile.items() if v is not None and k not in ("lat", "lon")]
            if parts:
                lines.append("Farm profile: " + ", ".join(parts))
        if crop:
            lines.append(f"Selected crop: {crop}")
        if plan.get("sowing_window"):
            lines.append(
                f"Sowing window: {plan['sowing_window'].get('start')} to {plan['sowing_window'].get('end')}"
            )
        if plan.get("harvest_window"):
            lines.append(
                f"Harvest window: {plan['harvest_window'].get('start')} to {plan['harvest_window'].get('end')}"
            )
        if plan.get("fertilizer_schedule"):
            items = "; ".join(
                f"{i['name']} ({i.get('amount_kg_per_acre')} kg/acre, {i.get('date')}, {i.get('status')})"
                for i in plan["fertilizer_schedule"]
            )
            lines.append(f"Fertilizer schedule: {items}")
        if plan.get("irrigation_schedule"):
            items = "; ".join(f"{i['date']}: {i['note']}" for i in plan["irrigation_schedule"])
            lines.append(f"Irrigation schedule: {items}")
        if plan.get("pest_risks"):
            items = "; ".join(
                f"{p['name']} ({p['risk_window_start']} to {p['risk_window_end']}, {p['status']})"
                for p in plan["pest_risks"]
            )
            lines.append(f"Pest/disease watch: {items}")
        if financials:
            item_lines = "; ".join(f"{i['label']} ৳{i['amount']:,}" for i in financials.get("items", []))
            lines.append(
                f"Financial breakdown - {item_lines}. Total cost ৳{financials.get('cost', 0):,}, "
                f"revenue ৳{financials.get('revenue', 0):,}, profit ৳{financials.get('profit', 0):,}, "
                f"ROI {financials.get('roi', 0)}%, break-even {financials.get('breakEvenTons', 0)} tons."
            )

        text = "\n".join(lines) if lines else "Nothing on the dashboard yet."
        trace.append(_trace_entry("farm_dashboard", {}, text, "dashboard", "read farmer's own dashboard data"))
        return text

    return farm_dashboard


def _make_kb_tool(crop: str | None, trace: list[dict], docs_acc: list[dict]) -> Callable:
    @tool
    def knowledge_base(query: str) -> str:
        """Search the grounded agricultural knowledge base (BARC's Hand Book
        of Agricultural Technology) for agronomic how-to information —
        fertilizer rates, irrigation timing, pest and disease control,
        planting technique, crop duration and yield. Pass a specific,
        focused query."""
        db = SessionLocal()
        try:
            docs = retrieve_agri_knowledge(db, query, crop=crop)
        finally:
            db.close()

        if not is_grounded_enough(docs):
            text = "Nothing relevant found in the knowledge base for this — try a web search instead."
            trace.append(
                _trace_entry(
                    "knowledge_base", {"query": query}, text, "knowledge",
                    f'0 relevant chunks for "{query}"',
                )
            )
            return text

        docs_acc.extend(docs)
        content = "\n\n".join(d["content"] for d in docs)
        trace.append(
            _trace_entry(
                "knowledge_base", {"query": query}, content, "knowledge",
                f'{len(docs)} chunks retrieved for "{query}"',
            )
        )
        return content

    return knowledge_base


def _make_web_tool(trace: list[dict], docs_acc: list[dict]) -> Callable:
    @tool
    def web_search(query: str) -> str:
        """Search the live web. Only use this when knowledge_base came back
        empty or clearly irrelevant, or the question needs something a
        farming reference wouldn't have (e.g. current market prices, news).
        Never use this for current weather — use current_weather instead."""
        docs = web_search_as_docs(query)
        if not docs:
            text = "The web search returned nothing usable."
            trace.append(
                _trace_entry("web_search", {"query": query}, text, "knowledge", f'web search for "{query}" returned nothing')
            )
            return text

        docs_acc.extend(docs)
        content = "\n\n".join(f"{d['source_title']} ({d['url']}): {d['content']}" for d in docs)
        trace.append(
            _trace_entry(
                "web_search", {"query": query}, content, "knowledge",
                f'{len(docs)} web results for "{query}"',
            )
        )
        return content

    return web_search


def _make_weather_tool(profile: dict, trace: list[dict]) -> Callable:
    @tool
    def current_weather(location: str | None = None) -> str:
        """Get the live weather forecast (daily rainfall, max/min temperature
        for roughly the next 14 days) for the farmer's own farm, or for a
        different place if the farmer names one explicitly. Leave location
        empty to use the farmer's own farm location."""
        place = location or profile.get("location")
        if not place:
            text = "No location available yet — the farm's location hasn't been set."
            trace.append(_trace_entry("current_weather", {"location": location}, text, "weather", "no location to look up"))
            return text

        if location:
            geo = geocode_location(place)
            if not geo:
                text = f"Couldn't resolve the location '{place}'."
                trace.append(_trace_entry("current_weather", {"location": place}, text, "weather", "geocoding failed"))
                return text
            lat, lon = geo["lat"], geo["lon"]
        else:
            lat, lon = profile.get("lat"), profile.get("lon")
            if lat is None or lon is None:
                geo = geocode_location(place)
                if not geo:
                    text = f"Couldn't resolve the location '{place}'."
                    trace.append(_trace_entry("current_weather", {"location": place}, text, "weather", "geocoding failed"))
                    return text
                lat, lon = geo["lat"], geo["lon"]

        forecast = get_weather_forecast(lat, lon)
        if not forecast:
            text = "The weather service is unavailable right now."
            trace.append(_trace_entry("current_weather", {"location": place}, text, "weather", "forecast unavailable"))
            return text

        rows = list(
            zip(
                forecast["dates"],
                forecast["daily_rainfall_mm"],
                forecast["daily_temp_max_c"],
                forecast["daily_temp_min_c"],
            )
        )
        lines = [f"{d}: {rain}mm rain, {tmax}-{tmin}C" for d, rain, tmax, tmin in rows[:7]]
        text = f"Forecast for {place} (next 7 of {len(rows)} days): " + "; ".join(lines)
        trace.append(
            _trace_entry(
                "current_weather", {"location": place}, text, "weather",
                f"{len(rows)}-day forecast retrieved for {place}, "
                f"{sum(forecast['daily_rainfall_mm']):.0f}mm total rainfall",
            )
        )
        return text

    return current_weather


def qa_agent(state: AgentState) -> dict:
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    query = last_human.content if last_human else ""

    profile = state.get("farm_profile") or {}
    crop = state.get("selected_crop")

    trace: list[dict] = []
    docs_acc: list[dict] = []

    tools = [
        _make_dashboard_tool(state, trace),
        _make_kb_tool(crop, trace, docs_acc),
        _make_web_tool(trace, docs_acc),
        _make_weather_tool(profile, trace),
    ]

    # reasoning_effort="none": settings.chat_model is a reasoning model, and
    # OpenAI's /v1/chat/completions rejects function tools together with a
    # reasoning effort on this model ("Function tools with reasoning_effort
    # are not supported ... set reasoning_effort to 'none'") — every other
    # node uses this same model without tools bound, so this is the one spot
    # that needs it turned off explicitly.
    llm = ChatOpenAI(
        model=settings.chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
        reasoning_effort="none",
    )
    agent = create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)

    result = agent.invoke({"messages": [*_build_history(state), HumanMessage(content=query)]})

    final_message = result["messages"][-1]
    answer = final_message.content or "I wasn't able to put together an answer for that."

    update: dict = {
        "trace_log": trace,
        "turn_complete": True,
        "messages": [AIMessage(content=answer)],
    }
    if docs_acc:
        update["retrieved_docs"] = docs_acc
    return update
