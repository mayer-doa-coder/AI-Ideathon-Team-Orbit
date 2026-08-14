"""Applies the specific adjustment `compare_thresholds` decided on to a
fresh copy of the season plan — never mutates the input, so `state["season_plan"]`
still reflects what was committed before this sweep if anything downstream
needs to compare before/after.
"""
import copy
from datetime import date, timedelta

from app.agents.monitor_nodes.compare_thresholds import RUNOFF_DELAY_DAYS
from app.agents.state import MonitorState
from app.db.trace import log_trace


def _apply_runoff_delay(plan: dict, ctx: dict) -> None:
    for item in plan.get("fertilizer_schedule", []):
        if item["name"] == ctx["item_name"] and item["date"] == ctx["item_date"]:
            new_date = (date.fromisoformat(item["date"]) + timedelta(days=RUNOFF_DELAY_DAYS)).isoformat()
            item["adjustment_note"] = (
                f"Delayed from {item['date']} to {new_date} — {ctx['rain_mm']:.0f}mm rain "
                f"forecast would wash the nutrients away before uptake."
            )
            item["date_before_adjustment"] = item["date"]
            item["date"] = new_date
            item["adjusted"] = True
            return


def _apply_pest_warning(plan: dict, ctx: dict) -> None:
    for item in plan.get("pest_risks", []):
        if item["name"] == ctx["item_name"]:
            item["status"] = "active"
            item["adjusted"] = True
            item["adjustment_note"] = (
                f"Conditions now favor {item['name']} ({ctx['rain_mm']:.0f}mm rain forecast) — "
                f"preventive treatment recommended before the window opens."
            )
            return


def recompute_season_plan(state: MonitorState) -> dict:
    if not state.get("triggered"):
        return {"updated_plan": None}

    ctx = state["trigger_context"]
    plan = copy.deepcopy(state["season_plan"])

    if ctx["type"] == "runoff_risk":
        _apply_runoff_delay(plan, ctx)
    elif ctx["type"] == "pest_risk":
        _apply_pest_warning(plan, ctx)

    log_trace(
        farm_id=state["farm_id"], source="monitor", node_name="recompute_season_plan",
        params={"trigger_context": ctx},
        result={"adjusted": True},
    )
    return {"updated_plan": plan}
