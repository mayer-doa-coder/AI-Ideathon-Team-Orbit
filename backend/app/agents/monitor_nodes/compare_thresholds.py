"""Checks the committed season plan's pending fertilizer and pest/disease
items against the fetched forecast, and decides whether anything needs to
change.

Two independent checks, first match wins for this sweep (the next sweep
will catch anything else — this keeps one alert focused on one change
rather than a wall of simultaneous warnings):

1. **Runoff risk** — a pending fertilizer application due soon, with heavy
   rain forecast around that date. Applying nitrogen right before a
   downpour washes it away before the crop can use it.
2. **Pest/disease risk window** — a tracked pest/disease's risk window
   opening soon, with sustained rain forecast. Bangladesh's major rice
   diseases (bacterial leaf blight, blast) spread fastest in humid,
   waterlogged conditions, so heavy rain is the leading indicator BARC's
   handbook ties to outbreak risk.
"""
from datetime import date, timedelta

from app.agents.state import MonitorState
from app.db.trace import log_trace

FERTILIZER_LOOKAHEAD_DAYS = 5
RUNOFF_RAIN_WINDOW_DAYS = 2
RUNOFF_RAIN_THRESHOLD_MM = 30.0
RUNOFF_DELAY_DAYS = 4

PEST_LOOKAHEAD_DAYS = 5
PEST_RAIN_CHECK_DAYS = 3
PEST_RAIN_THRESHOLD_MM = 25.0


def _rainfall_between(daily_by_date: dict, start: str, end: str) -> float:
    return sum(
        day["rainfall_mm"] for d, day in daily_by_date.items() if start <= d <= end
    )


def _check_runoff_risk(season_plan: dict, daily_by_date: dict, forecast_start: str) -> dict | None:
    for item in season_plan.get("fertilizer_schedule", []):
        if item.get("status") != "pending":
            continue
        if item.get("adjusted"):
            continue
        item_date = item["date"]
        days_out = (date.fromisoformat(item_date) - date.fromisoformat(forecast_start)).days
        if not (0 <= days_out <= FERTILIZER_LOOKAHEAD_DAYS):
            continue

        window_start = (date.fromisoformat(item_date) - timedelta(days=1)).isoformat()
        window_end = (date.fromisoformat(item_date) + timedelta(days=RUNOFF_RAIN_WINDOW_DAYS)).isoformat()
        rain_mm = _rainfall_between(daily_by_date, window_start, window_end)
        if rain_mm >= RUNOFF_RAIN_THRESHOLD_MM:
            return {
                "type": "runoff_risk",
                "item_name": item["name"],
                "item_date": item_date,
                "rain_mm": rain_mm,
            }
    return None


def _check_pest_risk(season_plan: dict, daily_by_date: dict, forecast_start: str) -> dict | None:
    check_end = (date.fromisoformat(forecast_start) + timedelta(days=PEST_RAIN_CHECK_DAYS)).isoformat()
    rain_mm = _rainfall_between(daily_by_date, forecast_start, check_end)
    if rain_mm < PEST_RAIN_THRESHOLD_MM:
        return None

    for item in season_plan.get("pest_risks", []):
        if item.get("adjusted"):
            continue
        window_start = item["risk_window_start"]
        days_out = (date.fromisoformat(window_start) - date.fromisoformat(forecast_start)).days
        if 0 <= days_out <= PEST_LOOKAHEAD_DAYS:
            return {
                "type": "pest_risk",
                "item_name": item["name"],
                "item_date": window_start,
                "rain_mm": rain_mm,
            }
    return None


def _human_reason(ctx: dict) -> str:
    if ctx["type"] == "runoff_risk":
        return (
            f"Runoff risk: {ctx['rain_mm']:.0f}mm rain forecast around the "
            f"{ctx['item_name']} application due {ctx['item_date']}"
        )
    return (
        f"Pest/disease risk: {ctx['rain_mm']:.0f}mm rain forecast in the next "
        f"{PEST_RAIN_CHECK_DAYS} days — conditions favor {ctx['item_name']}"
    )


def compare_thresholds(state: MonitorState) -> dict:
    weather = state.get("weather_data")
    season_plan = state["season_plan"]

    if not weather or not weather.get("daily"):
        log_trace(
            farm_id=state["farm_id"], source="monitor", node_name="compare_thresholds",
            result={"triggered": False, "reason": "no weather data available"},
        )
        return {"triggered": False, "trigger_reason": None, "trigger_context": None}

    daily_by_date = {day["date"]: day for day in weather["daily"]}
    forecast_start = weather["daily"][0]["date"]

    ctx = _check_runoff_risk(season_plan, daily_by_date, forecast_start)
    if ctx is None:
        ctx = _check_pest_risk(season_plan, daily_by_date, forecast_start)

    if ctx is None:
        log_trace(
            farm_id=state["farm_id"], source="monitor", node_name="compare_thresholds",
            params={"thresholds": {
                "runoff_rain_mm": RUNOFF_RAIN_THRESHOLD_MM,
                "pest_rain_mm": PEST_RAIN_THRESHOLD_MM,
            }},
            result={"triggered": False},
        )
        return {"triggered": False, "trigger_reason": None, "trigger_context": None}

    reason = _human_reason(ctx)
    log_trace(
        farm_id=state["farm_id"], source="monitor", node_name="compare_thresholds",
        params={"thresholds": {
            "runoff_rain_mm": RUNOFF_RAIN_THRESHOLD_MM,
            "pest_rain_mm": PEST_RAIN_THRESHOLD_MM,
        }},
        result={"triggered": True, "trigger_reason": reason, "trigger_context": ctx},
    )
    return {"triggered": True, "trigger_reason": reason, "trigger_context": ctx}
