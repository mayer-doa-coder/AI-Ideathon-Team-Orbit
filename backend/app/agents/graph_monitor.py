"""Builds and compiles the monitor graph, and provides the one entry point
(`run_monitor_sweep`) the scheduler and the on-demand API routes both call.

The monitor graph itself has no Postgres access — `season_plan`/`farm` are
loaded here, once, before invoking the graph, per the architecture's memory
design: the graph's "memory" of a farm is the `plans` table, not a
checkpointer. Only `write_alert` touches the database, to persist its
result back.
"""
from sqlalchemy.orm import Session

from app.agents.monitor_nodes.compare_thresholds import compare_thresholds
from app.agents.monitor_nodes.fetch_weather import fetch_weather
from app.agents.monitor_nodes.recompute_financials import recompute_financials
from app.agents.monitor_nodes.recompute_season_plan import recompute_season_plan
from app.agents.monitor_nodes.write_alert import write_alert
from app.agents.state import FarmProfile, MonitorState
from app.db.models import Farm, Plan
from langgraph.graph import END, START, StateGraph


def _route_after_compare(state: MonitorState) -> str:
    return "recompute_season_plan" if state["triggered"] else END


def build_monitor_graph():
    builder = StateGraph(MonitorState)

    builder.add_node("fetch_weather", fetch_weather)
    builder.add_node("compare_thresholds", compare_thresholds)
    builder.add_node("recompute_season_plan", recompute_season_plan)
    builder.add_node("recompute_financials", recompute_financials)
    builder.add_node("write_alert", write_alert)

    builder.add_edge(START, "fetch_weather")
    builder.add_edge("fetch_weather", "compare_thresholds")
    builder.add_conditional_edges(
        "compare_thresholds",
        _route_after_compare,
        {"recompute_season_plan": "recompute_season_plan", END: END},
    )
    builder.add_edge("recompute_season_plan", "recompute_financials")
    builder.add_edge("recompute_financials", "write_alert")
    builder.add_edge("write_alert", END)

    return builder.compile()


monitor_graph = build_monitor_graph()


def _farm_profile(farm: Farm) -> FarmProfile:
    return {
        "location": farm.location,
        "lat": farm.lat,
        "lon": farm.lon,
        "acres": farm.acres,
        "soil_type": farm.soil_type,
        "water_availability": farm.water_availability,
        "budget": farm.budget,
        "season": farm.season,
    }


def load_initial_state(
    db: Session, farm_id: int, weather_override: dict | None = None
) -> MonitorState | None:
    """Loads the farm + its committed plan and builds a fresh `MonitorState`.

    Returns None if the farm doesn't exist, is still mid-onboarding (any
    profile field still unset), or has no committed plan yet — the
    conversation graph's `persist` node fills in `Farm`/`Plan` incrementally
    across turns, so both can legitimately exist half-populated; there's
    nothing for the monitor to protect until every field is real.
    """
    farm = db.get(Farm, farm_id)
    if farm is None or any(
        value is None
        for value in (
            farm.location, farm.lat, farm.lon, farm.acres,
            farm.soil_type, farm.water_availability, farm.budget, farm.season,
        )
    ):
        return None

    plan = db.query(Plan).filter(Plan.farm_id == farm_id).one_or_none()
    if plan is None or plan.season_plan is None or plan.financials is None:
        return None

    return {
        "farm_id": farm_id,
        "farm": _farm_profile(farm),
        "season_plan": plan.season_plan,
        "financials": plan.financials,
        "weather_data": None,
        "weather_override": weather_override,
        "triggered": False,
        "trigger_reason": None,
        "trigger_context": None,
        "updated_plan": None,
        "updated_financials": None,
    }


def run_monitor_sweep(
    db: Session, farm_id: int, weather_override: dict | None = None
) -> MonitorState | None:
    """Runs one full monitor sweep for a single farm. Returns the final
    state, or None if the farm has no active plan to check yet."""
    initial_state = load_initial_state(db, farm_id, weather_override=weather_override)
    if initial_state is None:
        return None
    return monitor_graph.invoke(initial_state)
