"""Deterministic Market Decision Engine — SELL NOW / STORE / WAIT.

Pure Python, no LLM call, same philosophy as `monitor_nodes/compare_thresholds.py`
and `tools/marketplace.py`'s ranking: a transparent weighted-factor scoring
model, not a black box and not machine-learned. Every factor that fires
appends a plain-language reason, so the verdict is always explainable in
terms of the actual data that produced it (see `reasons`).

`verdict` is `None` — never a guessed SELL_NOW/STORE/WAIT — when there
isn't enough real price data to ground a decision in. The agent must never
substitute its own judgment for this: `verdict` is the answer, an LLM node
only narrates it (see `agents/nodes/market_price_lookup.py`).
"""
from dataclasses import dataclass, field

from app.tools.market_analytics import MarketSnapshot

# Crop -> the season that is that crop's dominant harvest period in
# Bangladesh (i.e. when national supply peaks and prices are seasonally
# depressed). A real, if simplified, agronomic fact — not invented per
# request. Rice varies by variety/season already (see market_price.py's
# RICE_COMMODITY_BY_SEASON), so its harvest season is whichever season the
# resolved paddy variety belongs to.
HARVEST_SEASON_BY_CROP = {
    "wheat": "rabi",
    "maize": "rabi",
    "potato": "rabi",
    "mustard": "rabi",
    "mungbean": "zaid",
    "chickpea": "rabi",
    "onion": "rabi",
    "garlic": "rabi",
}

SELL_THRESHOLD = 12.0
STORE_THRESHOLD = -8.0
NEAR_EXTREME_PCT = 5.0  # "within 5% of the historical high/low" counts as being at that extreme

VERDICT_SELL_NOW = "SELL_NOW"
VERDICT_STORE = "STORE"
VERDICT_WAIT = "WAIT"


@dataclass
class MarketDecision:
    verdict: str | None  # "SELL_NOW" | "STORE" | "WAIT" | None (insufficient data)
    score: float | None
    reasons: list[str] = field(default_factory=list)
    factors: dict[str, float] = field(default_factory=dict)  # factor name -> its score contribution


def _harvest_season_for(crop: str, season: str | None) -> str | None:
    if crop == "rice":
        # For rice, the stated season already determined *which* paddy
        # variety's price data we fetched (Aus/Aman/Boro — see
        # tools/market_price.RICE_COMMODITY_BY_SEASON), so "does the season
        # match this crop's harvest season" would be tautologically true
        # every time and add no real signal beyond what the price/trend
        # data (already specific to that season's variety) already carries.
        return None
    return HARVEST_SEASON_BY_CROP.get(crop)


def make_decision(
    snapshot: MarketSnapshot,
    season: str | None = None,
    storage_available: bool | None = None,
    storage_cost_bdt_per_unit_per_month: float | None = None,
    quantity_kg: float | None = None,
    urgent_cash_needed: bool | None = None,
) -> MarketDecision:
    if not snapshot.has_data or snapshot.current_price is None:
        return MarketDecision(
            verdict=None,
            score=None,
            reasons=[snapshot.unavailable_reason or "No market-price data available to base a decision on."],
        )

    score = 0.0
    reasons: list[str] = []
    factors: dict[str, float] = {}

    def add(name: str, amount: float, reason: str) -> None:
        nonlocal score
        score += amount
        factors[name] = amount
        reasons.append(reason)

    if snapshot.historical_average:
        vs_avg_pct = (snapshot.current_price - snapshot.historical_average) / snapshot.historical_average * 100
        contribution = max(-18.0, min(18.0, vs_avg_pct * 0.6))
        if abs(vs_avg_pct) >= 3:
            direction = "above" if vs_avg_pct > 0 else "below"
            add(
                "price_vs_average",
                contribution,
                f"current price (৳{snapshot.current_price:.0f}/{snapshot.unit}) is {abs(vs_avg_pct):.0f}% "
                f"{direction} the {snapshot.observation_count}-observation historical average "
                f"(৳{snapshot.historical_average:.0f}/{snapshot.unit})",
            )

    if snapshot.trend == "rising":
        add("trend", -8.0, "the recent price trend is rising — waiting may capture a higher price")
    elif snapshot.trend == "falling":
        add("trend", 10.0, "the recent price trend is falling — selling now avoids a further drop")

    if snapshot.historical_high and snapshot.current_price >= snapshot.historical_high * (1 - NEAR_EXTREME_PCT / 100):
        add(
            "near_historical_high",
            8.0,
            f"current price is within {NEAR_EXTREME_PCT:.0f}% of the historical high "
            f"(৳{snapshot.historical_high:.0f}/{snapshot.unit}) — a strong time to sell",
        )
    elif snapshot.historical_low and snapshot.current_price <= snapshot.historical_low * (1 + NEAR_EXTREME_PCT / 100):
        add(
            "near_historical_low",
            -8.0,
            f"current price is within {NEAR_EXTREME_PCT:.0f}% of the historical low "
            f"(৳{snapshot.historical_low:.0f}/{snapshot.unit}) — selling now would lock in a weak price",
        )

    harvest_season = _harvest_season_for(snapshot.crop, season)
    if season and harvest_season:
        if season == harvest_season:
            add(
                "season_harvest_glut",
                -6.0,
                f"{season} is {snapshot.crop}'s harvest season nationally — prices are typically at their "
                "seasonal low from increased supply",
            )
        else:
            add(
                "season_lean_period",
                6.0,
                f"{season} is outside {snapshot.crop}'s harvest season — prices are typically firmer, "
                "a reasonable time to sell stored produce",
            )

    if urgent_cash_needed:
        add("urgent_cash", 20.0, "an urgent cash need means waiting isn't practical, regardless of price timing")

    if storage_available is False:
        add("no_storage", 8.0, "no storage is available — holding the crop risks spoilage or loss")
    elif storage_available is True:
        add("storage_available", -3.0, "storage is available, so waiting for a better price is a real option")

    if storage_available and storage_cost_bdt_per_unit_per_month and snapshot.current_price:
        monthly_cost_pct = storage_cost_bdt_per_unit_per_month / snapshot.current_price * 100
        if monthly_cost_pct >= 4:
            qty_note = f" for your {quantity_kg:.0f}{snapshot.unit}" if quantity_kg else ""
            add(
                "storage_cost",
                5.0,
                f"storage costs ~{monthly_cost_pct:.0f}% of the crop's value per month{qty_note} — "
                "holding for long erodes the margin",
            )

    if storage_available is False:
        verdict = VERDICT_SELL_NOW if score >= 0 else VERDICT_WAIT
    elif score >= SELL_THRESHOLD:
        verdict = VERDICT_SELL_NOW
    elif score <= STORE_THRESHOLD:
        verdict = VERDICT_STORE
    else:
        verdict = VERDICT_WAIT

    if not reasons:
        reasons.append(
            "price is close to its historical average with no strong trend, seasonal, or storage signal — "
            "no clear reason to sell now or hold, so waiting for a clearer signal is the safer default"
        )

    return MarketDecision(verdict=verdict, score=round(score, 1), reasons=reasons, factors=factors)
