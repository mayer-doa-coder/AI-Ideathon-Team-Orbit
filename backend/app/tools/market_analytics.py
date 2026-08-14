"""Market-price analytics — current price, historical average, 7/30-day
change, trend, and historical high/low — computed entirely from
`market_prices` rows already stored in Postgres (see
`scripts/ingest_market_prices.py`). This module makes no network calls;
DAM is slow (~20-30s/request) and only ever queried by the ingestion job.

Every stat here is `None` (or the whole result explicitly marked
insufficient) when the underlying rows don't support it — never estimated,
never carried forward from a different crop or a stale default. A
farmer/agent asking about a crop we haven't ingested data for, or one with
too few observations for a given calculation, gets an honest "not enough
data" rather than a fabricated number (see `MarketSnapshot.has_data`,
`.change_7d_pct` / `.change_30d_pct` / `.trend` being `None`).

Trend windows are tolerant date-distance comparisons, not a fixed pipeline
of named windows — "7-day change" compares the most recent observation to
whatever observation lands closest to 7 days earlier, within a tolerance
band, since DAM's real submission cadence is sparse and irregular (see
`tools/market_price.py`'s docstring). This is more robust to however dense
or sparse the actual ingested history turns out to be than assuming a
specific fixed set of windows exists.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models import MarketPrice
from app.tools.market_price import resolve_commodity

HISTORICAL_LOOKBACK_DAYS = 180
TREND_FLAT_THRESHOLD_PCT = 3.0  # smaller than this magnitude of change reads as "stable", not noise dressed up as a trend

# (days_back, tolerance) — how far back to look for a comparison point, and
# how much slack around that target date counts as "close enough" given
# DAM's irregular submission cadence.
CHANGE_WINDOWS = {
    "change_7d_pct": (7, 4),
    "change_30d_pct": (30, 8),
}


@dataclass
class MarketSnapshot:
    crop: str
    season: str | None
    dam_commodity_id: int | None
    dam_commodity_name: str | None
    district: str | None  # the district actually matched, or None if this is a national aggregate
    district_matched: bool  # False when the farmer's district had no data and this fell back to national
    unit: str | None
    has_data: bool
    current_price: float | None = None
    current_price_date: date | None = None
    historical_average: float | None = None
    historical_high: float | None = None
    historical_low: float | None = None
    change_7d_pct: float | None = None
    change_30d_pct: float | None = None
    trend: str | None = None  # "rising" | "falling" | "stable" | None (insufficient data)
    observation_count: int = 0
    markets: list[str] = field(default_factory=list)
    source: str | None = None
    source_url: str | None = None
    unavailable_reason: str | None = None


def _rows_for_crop(db: Session, crop: str, season: str | None, district: str | None) -> tuple[list[MarketPrice], bool]:
    """Returns (rows, district_matched). Prefers rows in the farmer's
    district; falls back to every stored row for this crop (national) if
    the district has none — never fails outright just because the exact
    district is missing."""
    commodity_entry = resolve_commodity(crop, season)
    if commodity_entry is None:
        return [], False
    dam_commodity_id = int(commodity_entry.split("|", 1)[0])

    cutoff = date.today() - timedelta(days=HISTORICAL_LOOKBACK_DAYS)
    base_query = db.query(MarketPrice).filter(
        MarketPrice.dam_commodity_id == dam_commodity_id,
        MarketPrice.price_date >= cutoff,
    )

    if district:
        district_rows = base_query.filter(MarketPrice.district.ilike(f"%{district}%")).order_by(MarketPrice.price_date).all()
        if district_rows:
            return district_rows, True

    return base_query.order_by(MarketPrice.price_date).all(), False


def _closest_row_near(rows: list[MarketPrice], target_date: date, tolerance_days: int) -> MarketPrice | None:
    candidates = [r for r in rows if abs((r.price_date - target_date).days) <= tolerance_days]
    if not candidates:
        return None
    return min(candidates, key=lambda r: abs((r.price_date - target_date).days))


def get_market_snapshot(
    db: Session,
    crop: str,
    season: str | None = None,
    district: str | None = None,
) -> MarketSnapshot:
    commodity_entry = resolve_commodity(crop, season)
    if commodity_entry is None:
        return MarketSnapshot(
            crop=crop,
            season=season,
            dam_commodity_id=None,
            dam_commodity_name=None,
            district=district,
            district_matched=False,
            unit=None,
            has_data=False,
            unavailable_reason=(
                f'"{crop}" has no corresponding commodity in DAM\'s price-reporting system — '
                "market intelligence isn't available for this crop."
            ),
        )

    dam_commodity_id_str, dam_commodity_name = commodity_entry.split("|", 1)
    rows, district_matched = _rows_for_crop(db, crop, season, district)

    if not rows:
        return MarketSnapshot(
            crop=crop,
            season=season,
            dam_commodity_id=int(dam_commodity_id_str),
            dam_commodity_name=dam_commodity_name,
            district=district,
            district_matched=False,
            unit=None,
            has_data=False,
            unavailable_reason=(
                f'No market-price data has been ingested yet for "{crop}"'
                + (f" in {district}" if district else "")
                + ". Run the DAM ingestion job, or check back once it has."
            ),
        )

    latest = rows[-1]
    markets = sorted({r.market for r in rows if r.market})

    snapshot = MarketSnapshot(
        crop=crop,
        season=season,
        dam_commodity_id=latest.dam_commodity_id,
        dam_commodity_name=latest.dam_commodity_name,
        district=latest.district if district_matched else None,
        district_matched=district_matched,
        unit=latest.unit,
        has_data=True,
        current_price=latest.avg_price,
        current_price_date=latest.price_date,
        historical_average=round(sum(r.avg_price for r in rows) / len(rows), 2),
        historical_high=max(r.max_price for r in rows),
        historical_low=min(r.min_price for r in rows),
        observation_count=len(rows),
        markets=markets,
        source=latest.source,
        source_url=latest.source_url,
    )

    for field_name, (days_back, tolerance) in CHANGE_WINDOWS.items():
        target = latest.price_date - timedelta(days=days_back)
        comparison = _closest_row_near(rows[:-1], target, tolerance)
        if comparison is None or comparison.avg_price == 0:
            continue
        pct = (latest.avg_price - comparison.avg_price) / comparison.avg_price * 100
        setattr(snapshot, field_name, round(pct, 1))

    if snapshot.change_30d_pct is not None:
        reference_change = snapshot.change_30d_pct
    elif snapshot.change_7d_pct is not None:
        reference_change = snapshot.change_7d_pct
    else:
        reference_change = None

    if reference_change is not None:
        if reference_change > TREND_FLAT_THRESHOLD_PCT:
            snapshot.trend = "rising"
        elif reference_change < -TREND_FLAT_THRESHOLD_PCT:
            snapshot.trend = "falling"
        else:
            snapshot.trend = "stable"

    return snapshot
