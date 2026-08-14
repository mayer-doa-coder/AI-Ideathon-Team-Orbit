from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.config import settings
from app.db.session import SessionLocal
from app.tools.market_analytics import get_market_snapshot
from app.tools.market_decision import make_decision

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "crop_recommendation.md"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class CropCandidateOut(BaseModel):
    name: str
    suitability: str
    water_need: str
    risk_level: str
    profit_estimate: float
    reasoning_knowledge: str
    reasoning_weather: str


class CropRecommendations(BaseModel):
    candidates: list[CropCandidateOut] = Field(min_length=3)


_llm = ChatOpenAI(
    model=settings.chat_model, temperature=0.3, api_key=settings.openai_api_key
).with_structured_output(CropRecommendations)


def _attach_market_intelligence(candidates: list[dict], profile: dict) -> None:
    """Best-effort, additive only: attaches real DAM-sourced current price,
    trend, and a SELL NOW/STORE/WAIT verdict to each candidate the crop
    recommendation already produced — never changes suitability/risk/profit
    or blocks the recommendation itself. Candidates whose crop has no DAM
    mapping (see tools/market_price.CROP_TO_COMMODITY) or no ingested data
    yet simply keep `market: None`, same as the standalone market-price
    agent path — no fabricated numbers, no broken recommendation flow."""
    season = profile.get("season")
    district = profile.get("location")

    db = SessionLocal()
    try:
        for candidate in candidates:
            try:
                snapshot = get_market_snapshot(db, crop=candidate["name"].lower(), season=season, district=district)
                if not snapshot.has_data:
                    continue
                decision = make_decision(snapshot, season=season)
                candidate["market"] = {
                    "current_price": snapshot.current_price,
                    "unit": snapshot.unit,
                    "historical_average": snapshot.historical_average,
                    "change_7d_pct": snapshot.change_7d_pct,
                    "change_30d_pct": snapshot.change_30d_pct,
                    "trend": snapshot.trend,
                    "verdict": decision.verdict,
                    "reasons": decision.reasons,
                    "source": snapshot.source,
                }
            except Exception:  # noqa: BLE001 — a market-data hiccup must never break crop recommendations
                continue
    finally:
        db.close()


def crop_recommendation(state: AgentState) -> dict:
    profile = state.get("farm_profile") or {}
    weather = state.get("weather_data")

    # Retrieval and the weather lookup now happen upstream, concurrently —
    # see nodes/knowledge_retrieval.py and the fan-out in
    # graph_conversation.py. This node is the join: it only does the LLM
    # ranking, over whatever both branches produced.
    #
    # `docs` may legitimately be empty if retrieval found nothing and the web
    # fallback also came back empty; the prompt below already handles a thin
    # context, and grounding is enforced by requiring each candidate to cite
    # its reasoning.
    docs = state.get("retrieved_docs") or []
    trace: list[dict] = []

    context_lines = [f"Farm profile: {profile}"]
    if weather:
        total_rain = sum(weather["daily_rainfall_mm"])
        context_lines.append(
            f"14-day forecast: {total_rain:.0f}mm total rainfall, "
            f"temps {min(weather['daily_temp_min_c'])}-{max(weather['daily_temp_max_c'])}°C"
        )
    else:
        context_lines.append("No weather forecast available for this location.")
    context_lines.append("Retrieved reference material:")
    for i, d in enumerate(docs, 1):
        context_lines.append(f"[{i}] (crop: {d['crop'] or 'general'}) {d['content']}")

    result: CropRecommendations = _llm.invoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(context_lines)},
        ]
    )

    candidates = [
        {
            "id": c.name.lower().replace(" ", "-"),
            "name": c.name,
            "suitability": c.suitability,
            "water_need": c.water_need,
            "risk_level": c.risk_level,
            "profit_estimate": c.profit_estimate,
            "reasoning_knowledge": c.reasoning_knowledge,
            "reasoning_weather": c.reasoning_weather,
            "market": None,
        }
        for c in result.candidates
    ]
    _attach_market_intelligence(candidates, profile)

    summary_lines = [f"Based on your profile, here are my top {len(candidates)} crop picks:"]
    for c in candidates:
        summary_lines.append(
            f"• {c['name']} — {c['suitability']} suitability, "
            f"~৳{c['profit_estimate']:,.0f} estimated profit"
        )
    summary_lines.append(
        "Check the crop comparison panel for the full reasoning, then tell me which one you'd like to go with."
    )

    return {
        "crop_candidates": candidates,
        "trace_log": trace,
        "turn_complete": True,
        "messages": [AIMessage(content="\n".join(summary_lines))],
    }
