from datetime import date, timedelta

from app.agents.nodes import season_planner as season_planner_module
from app.agents.nodes.season_planner import (
    FertilizerItem,
    IrrigationItem,
    PestRisk,
    SeasonPlanOut,
    WeedCheckpointItem,
    generate_season_plan,
)


def _fake_result(revised_acres=None):
    return SeasonPlanOut(
        sowing_start_days_from_today=0,
        sowing_end_days_from_today=2,
        harvest_start_days_after_sowing=100,
        harvest_end_days_after_sowing=110,
        fertilizer_schedule=[
            FertilizerItem(name="Urea", stage="basal", days_after_sowing=0, amount_kg_per_acre=30)
        ],
        irrigation_schedule=[IrrigationItem(days_after_sowing=10, note="irrigate")],
        pest_risks=[
            PestRisk(
                name="Stem borer",
                risk_window_start_days_after_sowing=20,
                risk_window_end_days_after_sowing=40,
                prevention="scout regularly",
            )
        ],
        weed_checkpoints=[WeedCheckpointItem(days_after_sowing=15, note="weed")],
        seed_rate_kg_per_acre=8.0,
        expected_yield_ton_per_acre=2.0,
        revised_acres=revised_acres,
        reasoning="test reasoning",
    )


class _FakeLLM:
    def __init__(self, result):
        self._result = result

    def invoke(self, messages):
        return self._result


def test_generate_season_plan_converts_day_offsets_to_real_dates(monkeypatch):
    monkeypatch.setattr(season_planner_module, "_llm", _FakeLLM(_fake_result()))

    plan, effective_acres = generate_season_plan(
        profile={"acres": 2.0}, crop="Rice", weather=None, docs=[], acres=2.0
    )

    today = date.today()
    assert plan["sowing_window"]["start"] == today.isoformat()
    assert plan["sowing_window"]["end"] == (today + timedelta(days=2)).isoformat()
    assert plan["fertilizer_schedule"][0]["status"] == "pending"
    assert plan["fertilizer_schedule"][0]["date"] == today.isoformat()
    assert plan["crop"] == "Rice"
    assert effective_acres == 2.0


def test_generate_season_plan_uses_revised_acres_when_set(monkeypatch):
    monkeypatch.setattr(season_planner_module, "_llm", _FakeLLM(_fake_result(revised_acres=1.2)))

    _, effective_acres = generate_season_plan(
        profile={"acres": 2.0}, crop="Rice", weather=None, docs=[], acres=2.0,
        extra_instruction="plant a smaller area",
    )

    assert effective_acres == 1.2


def test_generate_season_plan_falls_back_to_given_acres_when_not_revised(monkeypatch):
    monkeypatch.setattr(season_planner_module, "_llm", _FakeLLM(_fake_result(revised_acres=None)))

    _, effective_acres = generate_season_plan(
        profile={"acres": 3.5}, crop="Maize", weather=None, docs=[], acres=3.5
    )

    assert effective_acres == 3.5
