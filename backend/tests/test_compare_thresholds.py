"""Regression coverage for the schema-mismatch bug found 2026-07-24: the
monitor graph's `compare_thresholds` was only ever tested against
`scripts/seed_demo_farm.py`'s synthetic season_plan shape, not against what
the conversation graph's `season_planner` node actually produces — a real
farm's plan crashed with `KeyError: 'risk_window_start'` the moment forecast
rainfall crossed the pest threshold. These tests build a season_plan the
same way `season_planner.py` does (see `state.py::SeasonPlan`) so this can
never silently regress again.
"""
from datetime import date, timedelta

from app.agents.monitor_nodes.compare_thresholds import (
    PEST_RAIN_THRESHOLD_MM,
    RUNOFF_RAIN_THRESHOLD_MM,
    compare_thresholds,
)

# trace_log.farm_id is nullable and FK-constrained to a real farms row —
# use None so these tests don't need a real Farm fixture in the DB.
FARM_ID = None


def _d(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def _season_plan(**overrides) -> dict:
    plan = {
        "crop": "Rice",
        "sowing_window": {"start": _d(-10), "end": _d(-8)},
        "fertilizer_schedule": [
            {
                "name": "Urea (2nd split)", "stage": "tillering", "date": _d(3),
                "amount_kg_per_acre": 25, "status": "pending", "adjusted": False,
                "adjustment_note": None, "date_before_adjustment": None,
            },
        ],
        "irrigation_schedule": [],
        "pest_risks": [
            {
                "name": "Bacterial leaf blight", "risk_window_start": _d(2), "risk_window_end": _d(20),
                "status": "watching", "adjusted": False, "adjustment_note": None,
                "prevention": "Use resistant varieties, avoid excess nitrogen.",
            },
        ],
        "weed_checkpoints": [],
        "harvest_window": {"start": _d(90), "end": _d(100)},
        "seed_rate_kg_per_acre": 8.0,
        "expected_yield_ton_per_acre": 3.0,
        "reasoning": "test fixture",
    }
    plan.update(overrides)
    return plan


def _weather(rainfall_by_day: list[float]) -> dict:
    today = date.today()
    return {
        "lat": 23.7,
        "lon": 90.4,
        "daily": [
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "rainfall_mm": mm,
                "temp_max_c": 32.0,
                "temp_min_c": 24.0,
            }
            for i, mm in enumerate(rainfall_by_day)
        ],
    }


def _state(season_plan=None, weather=None):
    return {
        "farm_id": FARM_ID,
        "season_plan": season_plan if season_plan is not None else _season_plan(),
        "weather_data": weather,
    }


def test_real_conversation_agent_shaped_plan_does_not_crash():
    # This is the exact shape season_planner.py now produces and persist.py
    # writes to Postgres — must never raise, regardless of trigger outcome.
    heavy = [0.0] * 14
    result = compare_thresholds(_state(weather=_weather(heavy)))
    assert result["triggered"] is False


def test_runoff_risk_triggers_on_heavy_rain_near_pending_fertilizer():
    # Fertilizer due in 3 days (within FERTILIZER_LOOKAHEAD_DAYS=5), heavy
    # rain lands right on that window.
    rainfall = [0.0] * 14
    rainfall[3] = RUNOFF_RAIN_THRESHOLD_MM + 10
    result = compare_thresholds(_state(weather=_weather(rainfall)))
    assert result["triggered"] is True
    assert result["trigger_context"]["type"] == "runoff_risk"
    assert result["trigger_context"]["item_name"] == "Urea (2nd split)"


def test_applied_fertilizer_is_never_flagged_for_runoff():
    plan = _season_plan()
    plan["fertilizer_schedule"][0]["status"] = "applied"
    rainfall = [0.0] * 14
    # Day 5 falls inside the runoff window (item date ±1/+2 = days 2-5) but
    # outside the pest check's rain window (days 0-3), so this isolates the
    # runoff-skip behavior instead of accidentally tripping the pest check.
    rainfall[5] = RUNOFF_RAIN_THRESHOLD_MM + 10
    result = compare_thresholds(_state(season_plan=plan, weather=_weather(rainfall)))
    assert result["triggered"] is False


def test_pest_risk_triggers_on_sustained_rain_in_risk_window():
    # Heavy rain in the first 3 days (PEST_RAIN_CHECK_DAYS), pest risk
    # window opens in 2 days (within PEST_LOOKAHEAD_DAYS=5) — but keep the
    # fertilizer item far out so the runoff check doesn't win first.
    plan = _season_plan()
    plan["fertilizer_schedule"][0]["date"] = _d(30)
    rainfall = [0.0] * 14
    rainfall[0] = PEST_RAIN_THRESHOLD_MM + 10
    result = compare_thresholds(_state(season_plan=plan, weather=_weather(rainfall)))
    assert result["triggered"] is True
    assert result["trigger_context"]["type"] == "pest_risk"
    assert result["trigger_context"]["item_name"] == "Bacterial leaf blight"


def test_no_weather_data_does_not_trigger_or_crash():
    result = compare_thresholds(_state(weather=None))
    assert result["triggered"] is False


def test_mild_rain_does_not_trigger():
    result = compare_thresholds(_state(weather=_weather([2.0] * 14)))
    assert result["triggered"] is False
