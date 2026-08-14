"""Tests for market-price retrieval/trend analytics against the real dev
Postgres database (this project has no separate test-DB setup, and
MarketPrice rows are cheap to create/tear down — see conftest.py). Uses
crop="wheat" (a real DAM-mapped crop with no live data ingested for it as
of writing — confirmed by direct testing against DAM) and a private test
district, and clears all rows for that crop before *and* after every test
so results never depend on whatever real ingestion has or hasn't run.
"""
from datetime import date, timedelta

import pytest

from app.db.models import MarketPrice
from app.db.session import SessionLocal
from app.tools.market_analytics import get_market_snapshot

TEST_CROP = "wheat"
TEST_DISTRICT = "PytestDistrict"
SOURCE = "Bangladesh Department of Agricultural Marketing (DAM)"
SOURCE_URL = "https://market.dam.gov.bd/commodity_wise_report"


@pytest.fixture
def db():
    session = SessionLocal()
    session.query(MarketPrice).filter(MarketPrice.crop == TEST_CROP).delete()
    session.commit()
    try:
        yield session
    finally:
        session.query(MarketPrice).filter(MarketPrice.crop == TEST_CROP).delete()
        session.commit()
        session.close()


def _insert(db, price_date, avg, min_p=None, max_p=None, district=TEST_DISTRICT):
    db.add(
        MarketPrice(
            crop=TEST_CROP,
            dam_commodity_id=622,
            dam_commodity_name="গম",
            division="Test Division",
            district=district,
            market="Test Market",
            price_type="wholesale",
            unit="kg",
            min_price=min_p if min_p is not None else avg - 1,
            max_price=max_p if max_p is not None else avg + 1,
            avg_price=avg,
            period_start=price_date,
            period_end=price_date,
            price_date=price_date,
            source=SOURCE,
            source_url=SOURCE_URL,
        )
    )
    db.commit()


def test_current_price_retrieval_returns_most_recent_observation(db):
    today = date.today()
    _insert(db, today - timedelta(days=10), 30.0)
    _insert(db, today, 34.0)

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.has_data is True
    assert snapshot.current_price == 34.0
    assert snapshot.current_price_date == today
    assert snapshot.source == SOURCE


def test_historical_price_retrieval_computes_average_high_low(db):
    today = date.today()
    _insert(db, today - timedelta(days=60), 28.0, min_p=26.0, max_p=30.0)
    _insert(db, today - timedelta(days=30), 32.0, min_p=30.0, max_p=34.0)
    _insert(db, today, 36.0, min_p=34.0, max_p=38.0)

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.historical_average == round((28.0 + 32.0 + 36.0) / 3, 2)
    assert snapshot.historical_high == 38.0
    assert snapshot.historical_low == 26.0
    assert snapshot.observation_count == 3


def test_trend_calculation_detects_rising_price_and_pct_change(db):
    today = date.today()
    _insert(db, today - timedelta(days=30), 20.0)
    _insert(db, today - timedelta(days=7), 22.0)
    _insert(db, today, 25.0)

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.change_7d_pct == pytest.approx((25.0 - 22.0) / 22.0 * 100, rel=1e-2)
    assert snapshot.change_30d_pct == pytest.approx((25.0 - 20.0) / 20.0 * 100, rel=1e-2)
    assert snapshot.trend == "rising"


def test_trend_calculation_detects_falling_price(db):
    today = date.today()
    _insert(db, today - timedelta(days=30), 40.0)
    _insert(db, today, 30.0)

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.change_30d_pct == pytest.approx(-25.0, rel=1e-2)
    assert snapshot.trend == "falling"


def test_district_match_is_preferred_over_national_aggregate(db):
    today = date.today()
    _insert(db, today, 30.0, district="SomeOtherDistrict")
    _insert(db, today, 45.0, district=TEST_DISTRICT)

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.district_matched is True
    assert snapshot.current_price == 45.0


def test_falls_back_to_national_when_district_has_no_data(db):
    today = date.today()
    _insert(db, today, 30.0, district="SomeOtherDistrict")

    snapshot = get_market_snapshot(db, TEST_CROP, district="DistrictWithNoData")

    assert snapshot.has_data is True
    assert snapshot.district_matched is False
    assert snapshot.current_price == 30.0


def test_insufficient_data_when_nothing_ingested_yet(db):
    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.has_data is False
    assert snapshot.current_price is None
    assert snapshot.unavailable_reason is not None


def test_insufficient_data_when_crop_has_no_dam_mapping(db):
    snapshot = get_market_snapshot(db, "lentil")

    assert snapshot.has_data is False
    assert "lentil" in snapshot.unavailable_reason.lower()


def test_change_pct_is_none_when_no_comparable_observation_exists(db):
    today = date.today()
    _insert(db, today, 30.0)  # only one observation, nothing to compare against

    snapshot = get_market_snapshot(db, TEST_CROP, district=TEST_DISTRICT)

    assert snapshot.has_data is True
    assert snapshot.change_7d_pct is None
    assert snapshot.change_30d_pct is None
    assert snapshot.trend is None  # no fabricated trend without a real comparison point
