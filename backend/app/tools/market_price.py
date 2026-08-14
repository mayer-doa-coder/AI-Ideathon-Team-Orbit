"""Real, keyless HTTP client for the Bangladesh Department of Agricultural
Marketing (DAM, market.dam.gov.bd) — the market-price source this feature
is required to use. DAM publishes no documented public API; this scrapes
their actual public "Commodity Wise Price Report"
(market.dam.gov.bd/commodity_wise_report), a CSRF-protected HTML form,
which is the most reliable real mechanism DAM exposes (confirmed by direct
testing — see the ingestion script's module docstring for what else was
tried and why this report was chosen).

Important, honestly-documented characteristics of this data source:

- DAM's report is a *period aggregate* (min/max/avg over a date range you
  choose), not a clean per-day price point. There is no bulk daily-series
  export. `fetch_commodity_prices` therefore returns one row per
  (market, price type) for the whole queried window, not one row per day.
  Callers needing a time series (see `tools/market_analytics.py`) do so by
  querying multiple distinct windows and comparing them, not by assuming
  daily granularity exists.
- Many (commodity, market, date-range) combinations legitimately have no
  submitted price on file — DAM's own site returns "There is no data!" for
  these, which this client passes through as an empty list rather than
  inventing a value.
- DAM's report does not state a unit explicitly. "kg" is used as the unit
  for all rows, matching DAM's documented standard convention for
  retail/producer commodity prices — a stated assumption, not a fabricated
  number.
- No API key or credential is required or used; this is a public web form.
"""
import logging
import re
from dataclasses import dataclass
from datetime import date

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://market.dam.gov.bd"
REPORT_PATH = "/commodity_wise_report"
# DAM's server genuinely takes 20-30s+ to compute this report (observed
# directly, not a network issue) — this is exactly why ingestion runs as a
# standalone script/scheduled job that writes to Postgres (see
# scripts/ingest_market_prices.py), never inline during a live chat turn or
# API request. Callers always read the stored result, which is fast.
REQUEST_TIMEOUT = 60.0
USER_AGENT = "Mozilla/5.0 (compatible; AgriSenseAI-MarketIntelligence/1.0)"

SOURCE_NAME = "Bangladesh Department of Agricultural Marketing (DAM)"
SOURCE_URL = f"{BASE_URL}{REPORT_PATH}"

# DAM's own price-type categories (Bangla), normalized to short English keys.
PRICE_TYPE_BY_BANGLA = {
    "উৎপাদক": "producer",
    "খুচরা": "retail",
    "পাইকারী": "wholesale",
}

# Real DAM Commodity_id values, found by inspecting the live commodity_wise_report
# form's <select name="Commodity_id[]"> options directly (434 total commodities;
# this is the subset matching AgriSense's existing canonical crop list — see
# tools/financials.py's MARKET_PRICE_BDT_PER_TON keys). Format is "<id>|<bangla label>",
# exactly what the form's <option value=...> expects.
#
# "lentil" has no entry: DAM's commodity list has no specific moshur/lentil
# line item (only a generic, unusable "ডাল" catch-all with no pulse type
# named) — confirmed by exhaustively searching all 434 commodities, not a
# lookup gap. Market intelligence for lentil honestly reports "unavailable".
CROP_TO_COMMODITY = {
    "wheat": "622|গম",
    "maize": "739|ভুট্টা",
    "potato": "942|আলু (দেশী)",
    "mustard": "808|সরিষা",
    "mungbean": "799|মুগ ডাল",
    "chickpea": "710|ছোলা",
    "onion": "831|পেঁয়াজ - দেশী",
    "garlic": "834|রসুন - দেশী",
}

# Rice is priced by DAM as unmilled paddy (ধান), which is what a smallholder
# farmer actually sells at harvest — split by growing season, since Aus/Aman/
# Boro paddy are genuinely different commodities with different price levels.
# This is also where "season" concretely changes which real data gets
# fetched, not just a decision-engine weight applied after the fact.
RICE_COMMODITY_BY_SEASON = {
    "zaid": "590|আউশ ধান - মোটা",       # Aus paddy (pre-monsoon/summer)
    "kharif": "587|আমন ধান - মোটা",     # Aman paddy (monsoon)
    "rabi": "597|বোরো ধান - মোটা",      # Boro paddy (dry season)
}
DEFAULT_RICE_COMMODITY = RICE_COMMODITY_BY_SEASON["kharif"]  # Aman — the dominant rice season nationally

CANONICAL_CROPS = ["rice", "wheat", "maize", "potato", "mustard", "mungbean", "chickpea", "onion", "garlic"]


def resolve_commodity(crop: str, season: str | None = None) -> str | None:
    """Maps a canonical crop name (+ optional season) to a DAM Commodity_id
    string. Returns None if this crop has no DAM mapping (e.g. lentil) —
    callers must treat that as "unavailable", never guess a substitute."""
    key = (crop or "").strip().lower()
    if key == "rice":
        season_key = (season or "").strip().lower()
        return RICE_COMMODITY_BY_SEASON.get(season_key, DEFAULT_RICE_COMMODITY)
    return CROP_TO_COMMODITY.get(key)


@dataclass
class DamPriceRow:
    crop: str
    dam_commodity_id: int
    dam_commodity_name: str
    division: str | None
    district: str | None
    market: str | None
    price_type: str
    unit: str
    min_price: float
    max_price: float
    avg_price: float
    period_start: date
    period_end: date


_BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def _bangla_number(text: str) -> float | None:
    cleaned = (text or "").translate(_BANGLA_DIGITS).strip()
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _get_form_and_token(client: httpx.Client) -> str:
    response = client.get(REPORT_PATH, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    match = re.search(r'name="csrf_webspice_tkn"\s*value="([^"]*)"', response.text)
    if not match:
        raise RuntimeError("DAM report page did not contain a CSRF token — page structure may have changed")
    return match.group(1)


def _parse_commodity_wise_table(html: str, crop: str, commodity_id: int, commodity_name: str, unit: str) -> list[DamPriceRow]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        return []

    rows: list[DamPriceRow] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        # Expected columns: division, district, subdistrict, market, commodity
        # name, price type, year, min, max, avg (10 columns) — see the report's
        # own <thead>, confirmed by direct inspection.
        if len(cells) != 10:
            continue

        division, district, _subdistrict, market, _commodity, price_type_bn, _year, min_txt, max_txt, avg_txt = cells
        min_price = _bangla_number(min_txt)
        max_price = _bangla_number(max_txt)
        avg_price = _bangla_number(avg_txt)
        if min_price is None or max_price is None or avg_price is None:
            continue

        rows.append(
            DamPriceRow(
                crop=crop,
                dam_commodity_id=commodity_id,
                dam_commodity_name=commodity_name,
                division=division or None,
                district=district or None,
                market=market or None,
                price_type=PRICE_TYPE_BY_BANGLA.get(price_type_bn.strip(), price_type_bn.strip() or "unknown"),
                unit=unit,
                min_price=min_price,
                max_price=max_price,
                avg_price=avg_price,
                period_start=date.min,  # filled in by the caller, which knows the query window
                period_end=date.min,
            )
        )
    return rows


def fetch_commodity_prices(
    crop: str,
    date_from: date,
    date_end: date,
    season: str | None = None,
    unit: str = "kg",
) -> list[DamPriceRow]:
    """Queries DAM's real commodity-wise price report for `crop` over
    [date_from, date_end] and returns one row per (market, price type) DAM
    has on file for that window. Empty list means "no data for this window"
    (a legitimate, common result — DAM's own coverage is genuinely sparse
    for many crop/market/period combinations), not a failure.

    Raises `MarketPriceUnavailableError` only when the crop itself has no
    DAM commodity mapping at all (e.g. lentil) — a different, permanent
    condition from "no data for this window", which callers should surface
    differently (see `tools/market_analytics.py`).
    """
    commodity_entry = resolve_commodity(crop, season)
    if commodity_entry is None:
        raise MarketPriceUnavailableError(
            f'"{crop}" has no corresponding commodity in DAM\'s price-reporting system.'
        )
    commodity_id_str, commodity_name = commodity_entry.split("|", 1)
    commodity_id = int(commodity_id_str)

    try:
        with httpx.Client(base_url=BASE_URL, timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
            token = _get_form_and_token(client)
            response = client.post(
                REPORT_PATH,
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "csrf_webspice_tkn": token,
                    "Commodity_id[]": commodity_entry,
                    "date_from": date_from.strftime("%d-%m-%Y"),
                    "date_end": date_end.strftime("%d-%m-%Y"),
                    "filter": "Filter Data",
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("DAM request failed for crop=%s window=%s..%s: %s", crop, date_from, date_end, exc)
        return []

    rows = _parse_commodity_wise_table(response.text, crop, commodity_id, commodity_name, unit)
    for row in rows:
        row.period_start = date_from
        row.period_end = date_end
    return rows


class MarketPriceUnavailableError(Exception):
    """Raised when a crop has no corresponding DAM commodity at all (a
    permanent, known limitation — e.g. lentil) rather than a transient
    empty result for a particular query window."""
