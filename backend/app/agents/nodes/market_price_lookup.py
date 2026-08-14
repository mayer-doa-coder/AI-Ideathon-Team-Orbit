"""Tier 2/3: answers "should I sell my rice now?" style questions using
real DAM-sourced market prices (`tools/market_analytics.py`) and the
deterministic Market Decision Engine (`tools/market_decision.py`) — never
an LLM-guessed verdict (see that module's docstring). No LLM call needed
here; the extraction already happened in `classify_intent`.

Emits four separate trace_log entries (current price, historical prices,
trend analysis, decision engine) per the "visible agent trace" requirement,
even though they're all read from one `get_market_snapshot` call — each
entry surfaces a genuinely distinct facet of that same real result, not a
fabricated extra tool call.
"""
from langchain_core.messages import AIMessage

from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.tools.market_analytics import MarketSnapshot, get_market_snapshot
from app.tools.market_decision import MarketDecision, make_decision

VERDICT_LABELS = {
    "SELL_NOW": "SELL NOW",
    "STORE": "STORE",
    "WAIT": "WAIT",
}


def _trace_entry(entry_type: str, tool: str, params_display: str, params: dict, response: dict, summary: str) -> dict:
    return {
        "type": entry_type,
        "tool": tool,
        "paramsDisplay": params_display,
        "params": params,
        "response": response,
        "summary": summary,
    }


def _build_trace(snapshot: MarketSnapshot, decision: MarketDecision, params: dict) -> list[dict]:
    trace = []

    trace.append(
        _trace_entry(
            "market_price",
            "get_current_price",
            f'crop="{snapshot.crop}", district={snapshot.district or "any"}',
            {"crop": snapshot.crop, "season": snapshot.season, "district": params.get("district")},
            {
                "current_price": snapshot.current_price,
                "current_price_date": snapshot.current_price_date.isoformat() if snapshot.current_price_date else None,
                "unit": snapshot.unit,
                "district_matched": snapshot.district_matched,
                "markets": snapshot.markets,
            },
            (
                f"৳{snapshot.current_price:.0f}/{snapshot.unit} as of {snapshot.current_price_date}"
                if snapshot.has_data
                else "no current price on file"
            ),
        )
    )

    trace.append(
        _trace_entry(
            "market_price",
            "get_historical_prices",
            f'crop="{snapshot.crop}", lookback=180d',
            {"crop": snapshot.crop, "season": snapshot.season},
            {
                "historical_average": snapshot.historical_average,
                "historical_high": snapshot.historical_high,
                "historical_low": snapshot.historical_low,
                "observation_count": snapshot.observation_count,
            },
            (
                f"{snapshot.observation_count} observation(s), avg ৳{snapshot.historical_average:.0f}/{snapshot.unit}"
                if snapshot.has_data
                else "no historical data on file"
            ),
        )
    )

    trace.append(
        _trace_entry(
            "market_price",
            "analyze_trend",
            f'crop="{snapshot.crop}"',
            {"crop": snapshot.crop},
            {"change_7d_pct": snapshot.change_7d_pct, "change_30d_pct": snapshot.change_30d_pct, "trend": snapshot.trend},
            (
                f"trend={snapshot.trend or 'insufficient data'}"
                + (f", 7d={snapshot.change_7d_pct:+.1f}%" if snapshot.change_7d_pct is not None else "")
                + (f", 30d={snapshot.change_30d_pct:+.1f}%" if snapshot.change_30d_pct is not None else "")
            ),
        )
    )

    trace.append(
        _trace_entry(
            "market_price",
            "market_decision_engine",
            f'crop="{snapshot.crop}", season={params.get("season") or "unknown"}',
            {
                "season": params.get("season"),
                "storage_available": params.get("storage_available"),
                "urgent_cash_needed": params.get("urgent_cash_needed"),
                "quantity_kg": params.get("quantity_kg"),
            },
            {"verdict": decision.verdict, "score": decision.score, "factors": decision.factors, "reasons": decision.reasons},
            f"verdict={decision.verdict or 'insufficient data'}" + (f" (score={decision.score})" if decision.score is not None else ""),
        )
    )

    return trace


def _format_message(snapshot: MarketSnapshot, decision: MarketDecision) -> str:
    if not snapshot.has_data:
        return snapshot.unavailable_reason or f"I don't have market-price data for {snapshot.crop} yet."

    lines = [
        f"**{snapshot.crop.title()}** — ৳{snapshot.current_price:.0f}/{snapshot.unit} "
        f"as of {snapshot.current_price_date} ({snapshot.dam_commodity_name})."
    ]
    if snapshot.historical_average:
        lines.append(
            f"Historical average: ৳{snapshot.historical_average:.0f}/{snapshot.unit} "
            f"(range ৳{snapshot.historical_low:.0f}–{snapshot.historical_high:.0f}, {snapshot.observation_count} observations)."
        )
    change_parts = []
    if snapshot.change_7d_pct is not None:
        change_parts.append(f"7-day: {snapshot.change_7d_pct:+.1f}%")
    if snapshot.change_30d_pct is not None:
        change_parts.append(f"30-day: {snapshot.change_30d_pct:+.1f}%")
    if change_parts:
        lines.append(" | ".join(change_parts) + f" ({snapshot.trend or 'no clear trend'}).")

    if decision.verdict:
        lines.append(f"\n**Verdict: {VERDICT_LABELS.get(decision.verdict, decision.verdict)}**")
    else:
        lines.append("\nI don't have enough data to give a confident sell/store/wait verdict yet.")
    for reason in decision.reasons:
        lines.append(f"- {reason}")

    lines.append(f"\n_Source: {snapshot.source}._")
    return "\n".join(lines)


def market_price_lookup(state: AgentState) -> dict:
    query = state.get("market_price_query") or {}
    profile = state.get("farm_profile") or {}
    crop = (query.get("crop") or "").strip().lower()

    if not crop:
        return {
            "turn_complete": True,
            "messages": [AIMessage(content="Which crop would you like market-price information for?")],
        }

    season = profile.get("season")
    district = query.get("district") or profile.get("location")
    storage_available = query.get("storage_available")
    urgent_cash_needed = query.get("urgent_cash_needed")
    quantity_kg = query.get("quantity_kg")
    storage_cost = query.get("storage_cost_bdt_per_unit_per_month")

    db = SessionLocal()
    try:
        snapshot = get_market_snapshot(db, crop=crop, season=season, district=district)
    finally:
        db.close()

    decision = make_decision(
        snapshot,
        season=season,
        storage_available=storage_available,
        storage_cost_bdt_per_unit_per_month=storage_cost,
        quantity_kg=quantity_kg,
        urgent_cash_needed=urgent_cash_needed,
    )

    trace = _build_trace(
        snapshot,
        decision,
        {
            "district": district,
            "season": season,
            "storage_available": storage_available,
            "urgent_cash_needed": urgent_cash_needed,
            "quantity_kg": quantity_kg,
        },
    )

    return {
        "trace_log": trace,
        "turn_complete": True,
        "messages": [AIMessage(content=_format_message(snapshot, decision))],
    }
