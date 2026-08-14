"""Pure unit tests for the deterministic Market Decision Engine — no DB, no
LLM, matching the style of test_financials.py. Feeds MarketSnapshot objects
directly so each scenario's inputs are explicit and the verdict is
reproducible."""
import pytest

from app.tools.market_analytics import MarketSnapshot
from app.tools.market_decision import make_decision


def _snapshot(**overrides):
    base = dict(
        crop="wheat",
        season=None,
        dam_commodity_id=622,
        dam_commodity_name="গম",
        district=None,
        district_matched=False,
        unit="kg",
        has_data=True,
        current_price=30.0,
        current_price_date=None,
        historical_average=30.0,
        historical_high=32.0,
        historical_low=28.0,
        change_7d_pct=None,
        change_30d_pct=None,
        trend=None,
        observation_count=3,
        markets=["Test Market"],
        source="Bangladesh Department of Agricultural Marketing (DAM)",
        source_url="https://market.dam.gov.bd/commodity_wise_report",
    )
    base.update(overrides)
    return MarketSnapshot(**base)


def test_sell_now_verdict_when_price_well_above_average_and_off_season():
    # wheat's harvest season is rabi (see HARVEST_SEASON_BY_CROP) — kharif is lean/off-season
    snapshot = _snapshot(current_price=37.5, historical_average=30.0, historical_high=40.0, historical_low=28.0)
    decision = make_decision(snapshot, season="kharif")
    assert decision.verdict == "SELL_NOW"
    assert decision.reasons  # always explainable, never a bare verdict


def test_store_verdict_when_price_well_below_average_and_harvest_season():
    snapshot = _snapshot(current_price=24.0, historical_average=30.0, historical_high=34.0, historical_low=20.0)
    decision = make_decision(snapshot, season="rabi", storage_available=True)  # rabi = wheat's harvest season
    assert decision.verdict == "STORE"
    assert decision.reasons


def test_wait_verdict_when_no_strong_signal():
    snapshot = _snapshot(current_price=30.0, historical_average=30.0, historical_high=32.0, historical_low=28.0, trend="stable")
    decision = make_decision(snapshot)  # no season, no storage, no urgency, price at average
    assert decision.verdict == "WAIT"
    assert decision.reasons  # still explains the "no clear signal" default


def test_season_measurably_moves_the_score():
    snapshot = _snapshot(current_price=31.0, historical_average=30.0, historical_high=40.0, historical_low=25.0)
    harvest = make_decision(snapshot, season="rabi")   # wheat's harvest season -> pulls toward STORE
    lean = make_decision(snapshot, season="kharif")     # off-season -> pulls toward SELL_NOW

    assert lean.score > harvest.score
    assert lean.score - harvest.score == pytest.approx(12.0, abs=0.1)


def test_season_can_flip_the_verdict_across_the_threshold():
    # Same price data, only the season differs -> the deterministic engine
    # must produce a different verdict, per "season must influence the
    # final verdict" (not just be a minor tiebreaker).
    snapshot = _snapshot(current_price=33.0, historical_average=30.0, historical_high=40.0, historical_low=25.0)
    lean = make_decision(snapshot, season="kharif")
    harvest = make_decision(snapshot, season="rabi")

    assert lean.verdict == "SELL_NOW"
    assert harvest.verdict == "WAIT"


def test_rice_season_does_not_double_count_as_a_harvest_season_signal():
    # For rice, the season already determined which paddy variety's price
    # data was fetched (see tools/market_price.py) — asking "is this the
    # harvest season" again would be tautologically true every time and
    # isn't a real independent signal, so it must not fire for rice.
    snapshot = _snapshot(crop="rice", current_price=30.0, historical_average=30.0, historical_high=32.0, historical_low=28.0)
    decision = make_decision(snapshot, season="kharif")
    assert "season_harvest_glut" not in decision.factors
    assert "season_lean_period" not in decision.factors


def test_urgent_cash_need_overrides_toward_sell_now():
    # Price below average would otherwise lean STORE — urgent cash need must override that.
    snapshot = _snapshot(current_price=27.0, historical_average=30.0, historical_high=34.0, historical_low=24.0)
    decision = make_decision(snapshot, urgent_cash_needed=True)
    assert decision.verdict == "SELL_NOW"
    assert any("urgent" in r.lower() for r in decision.reasons)


def test_no_storage_available_never_returns_store_verdict():
    snapshot = _snapshot(current_price=22.0, historical_average=30.0, historical_high=32.0, historical_low=20.0)
    decision = make_decision(snapshot, storage_available=False)
    assert decision.verdict != "STORE"


def test_high_storage_cost_pushes_away_from_storing():
    cheap = _snapshot(current_price=24.0, historical_average=30.0, historical_high=34.0, historical_low=20.0)
    expensive = _snapshot(current_price=24.0, historical_average=30.0, historical_high=34.0, historical_low=20.0)

    cheap_decision = make_decision(cheap, storage_available=True, storage_cost_bdt_per_unit_per_month=0.1)
    expensive_decision = make_decision(
        expensive, storage_available=True, storage_cost_bdt_per_unit_per_month=3.0, quantity_kg=500
    )

    assert expensive_decision.score > cheap_decision.score


def test_insufficient_data_returns_no_verdict_not_a_guess():
    snapshot = _snapshot(
        has_data=False,
        current_price=None,
        historical_average=None,
        historical_high=None,
        historical_low=None,
        observation_count=0,
        unavailable_reason="No market-price data has been ingested yet for this crop.",
    )
    decision = make_decision(snapshot)
    assert decision.verdict is None
    assert decision.score is None
    assert decision.reasons  # still explains why, never silent
