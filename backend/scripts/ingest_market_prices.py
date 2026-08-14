"""CLI: ingest real market prices from the Bangladesh Department of
Agricultural Marketing (DAM) into the `market_prices` table.

DAM has no documented API (confirmed by direct inspection — see
`tools/market_price.py`'s module docstring). Their real "Commodity Wise
Price Report" form is a *period aggregate* (min/max/avg over a date range),
not a daily series export, and their server is genuinely slow (~20-30s per
query) — this is why ingestion is a standalone script that writes to
Postgres, never a live call inside a chat turn or API request.

Each run fetches four windows per crop so `market_analytics.py` has
real, distinct periods to compare rather than one window doing double duty:
  - "recent"      : last 7 days    -> current-price proxy
  - "prior_week"  : 8-14 days ago  -> 7-day change comparison point
  - "prior_month" : 31-37 days ago -> 30-day change comparison point
  - "historical"  : last 180 days  -> historical average / high / low

Rice is split by growing season (Aus/Aman/Boro are different real
commodities with different prices) — three separate ingestions, one per
season, all stored under crop="rice" and disambiguated by
`dam_commodity_id` the same way retrieval resolves it (see
`tools/market_price.resolve_commodity`).

Coverage is genuinely sparse — many crop/window combinations return no
data, which DAM's own site reports honestly ("There is no data!") and this
script simply doesn't insert anything for. That's expected, not a bug; see
`app/tools/market_analytics.py` for how downstream code is required to
represent "insufficient data" rather than guess.

Usage (from the backend/ venv):
    python -m scripts.ingest_market_prices
    python -m scripts.ingest_market_prices --crops onion,potato   # faster dev iteration
"""
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from app.db.models import MarketPrice
from app.db.session import SessionLocal
from app.tools.market_price import (
    CANONICAL_CROPS,
    RICE_COMMODITY_BY_SEASON,
    SOURCE_NAME,
    SOURCE_URL,
    DamPriceRow,
    fetch_commodity_prices,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 4  # polite concurrency against a slow public government server

WINDOWS = {
    "recent": (7, 0),
    "prior_week": (14, 8),
    "prior_month": (37, 31),
    "historical": (180, 0),
}


def _window_dates(days_back_start: int, days_back_end: int) -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=days_back_start), today - timedelta(days=days_back_end)


def _fetch_one(crop: str, season: str | None, window_name: str) -> tuple[str, str | None, str, list[DamPriceRow]]:
    days_back_start, days_back_end = WINDOWS[window_name]
    date_from, date_end = _window_dates(days_back_start, days_back_end)
    try:
        rows = fetch_commodity_prices(crop, date_from, date_end, season=season)
    except Exception:
        logger.exception("Ingestion failed for crop=%s season=%s window=%s", crop, season, window_name)
        rows = []
    return crop, season, window_name, rows


def ingest(crops: list[str]) -> int:
    jobs: list[tuple[str, str | None]] = []
    for crop in crops:
        if crop == "rice":
            jobs.extend(("rice", season) for season in RICE_COMMODITY_BY_SEASON)
        else:
            jobs.append((crop, None))

    tasks = [(crop, season, window_name) for crop, season in jobs for window_name in WINDOWS]
    logger.info("Fetching %d (crop, season, window) combinations from DAM (this will take a while)...", len(tasks))

    all_rows: list[DamPriceRow] = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as pool:
        futures = [pool.submit(_fetch_one, crop, season, window_name) for crop, season, window_name in tasks]
        for future in as_completed(futures):
            crop, season, window_name, rows = future.result()
            label = f"{crop}" + (f"/{season}" if season else "")
            logger.info("  %s [%s]: %d row(s)", label, window_name, len(rows))
            all_rows.extend(rows)

    if not all_rows:
        logger.warning("No data returned from DAM for any requested crop/window — nothing to store.")
        return 0

    today = date.today()
    db = SessionLocal()
    try:
        # Re-running the same day replaces today's rows rather than duplicating
        # them; older days' history (from previous runs) is left untouched.
        db.query(MarketPrice).filter(MarketPrice.price_date == today).delete()

        db.add_all(
            MarketPrice(
                crop=row.crop,
                dam_commodity_id=row.dam_commodity_id,
                dam_commodity_name=row.dam_commodity_name,
                division=row.division,
                district=row.district,
                market=row.market,
                price_type=row.price_type,
                unit=row.unit,
                min_price=row.min_price,
                max_price=row.max_price,
                avg_price=row.avg_price,
                period_start=row.period_start,
                period_end=row.period_end,
                price_date=today,
                source=SOURCE_NAME,
                source_url=SOURCE_URL,
            )
            for row in all_rows
        )
        db.commit()
        logger.info("Stored %d market_prices row(s) for price_date=%s", len(all_rows), today)
        return len(all_rows)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest real market prices from DAM")
    parser.add_argument(
        "--crops",
        default=",".join(CANONICAL_CROPS),
        help=f"Comma-separated crop list (default: all — {', '.join(CANONICAL_CROPS)})",
    )
    args = parser.parse_args()
    crops = [c.strip().lower() for c in args.crops.split(",") if c.strip()]
    ingest(crops)


if __name__ == "__main__":
    main()
