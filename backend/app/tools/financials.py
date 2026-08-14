"""Deterministic cost/yield/ROI/break-even math. No LLM calls, no I/O — pure
function so its output is exactly reproducible for the same inputs and
always internally consistent (change an input, the numbers move correctly).

One implementation, shared by both graphs: the conversation graph's
`season_planner`/`calculate_financials` node, the monitor graph's
`recompute_financials` node, and `scripts/seed_demo_farm.py` all call
`calculate_financials` against the one `SeasonPlan` shape (`state.py`).
This used to be two parallel, differently-shaped functions — one persisted
`plans.financials` in the conversation agent's shape, the other in the
monitor's — which meant whichever graph wrote last silently determined what
shape the frontend's `FinancialBreakdown` component would try to read on
the next reload. Unifying on one function is what made that safe.

Price constants are static illustrative BDT reference estimates, not a live
market feed (Tier 2, not built) — call this out as mock/reference data in
the README per the hackathon's real-vs-mock disclosure requirement.
"""
import copy
import re

FERTILIZER_PRICE_BDT_PER_KG = {
    "urea": 27,
    "tsp": 34,
    "mp": 27,
    "dap": 30,
    "gypsum": 14,
    "zinc sulphate": 220,
    "boric acid": 240,
    "compost": 8,
    "cowdung": 3,
}
DEFAULT_FERTILIZER_PRICE_BDT_PER_KG = 30

SEED_PRICE_BDT_PER_KG = {
    "rice": 60,
    "wheat": 55,
    "maize": 220,
    "potato": 40,
    "mustard": 120,
    "lentil": 130,
    "mungbean": 150,
    "chickpea": 90,
    "onion": 900,
    "garlic": 250,
}
DEFAULT_SEED_PRICE_BDT_PER_KG = 80

MARKET_PRICE_BDT_PER_TON = {
    "rice": 28000,
    "wheat": 32000,
    "maize": 24000,
    "potato": 15000,
    "mustard": 55000,
    "lentil": 90000,
    "mungbean": 85000,
    "chickpea": 70000,
    "onion": 25000,
    "garlic": 60000,
}
DEFAULT_MARKET_PRICE_BDT_PER_TON = 25000

LAND_PREP_COST_BDT_PER_ACRE = 2500
IRRIGATION_COST_BDT_PER_ACRE = 1800
PEST_CONTROL_COST_BDT_PER_ACRE = 1200
LABOR_COST_BDT_PER_ACRE = 4500
POST_HARVEST_COST_BDT_PER_ACRE = 1500


def _fertilizer_price(name: str) -> float:
    # The LLM writes descriptive names ("Well-decomposed cowdung", "Urea
    # (1st split - basal)"), not the bare tags this table is keyed by — an
    # exact match would silently fall back to the (much higher) default
    # price for anything not phrased exactly like the key, badly
    # overcharging common items like cowdung. A raw substring match isn't
    # safe either — short keys like "mp" false-positive inside ordinary
    # words ("deco{mp}osed"), which is exactly how "Well-decomposed
    # cowdung" once got priced as MP instead of cowdung. Word-boundary
    # match instead, so a key only matches as a whole word/phrase.
    name_lower = name.strip().lower()
    for key, price in FERTILIZER_PRICE_BDT_PER_KG.items():
        if re.search(rf"\b{re.escape(key)}\b", name_lower):
            return price
    return DEFAULT_FERTILIZER_PRICE_BDT_PER_KG


def calculate_financials(season_plan: dict, crop: str, acres: float) -> dict:
    """
    `season_plan` is expected to carry (at minimum):
      - seed_rate_kg_per_acre: float
      - fertilizer_schedule: list[{"name": str, "amount_kg_per_acre": float, ...}]
      - expected_yield_ton_per_acre: float

    Returns a dict shaped to match the frontend FinancialBreakdown component:
      {items: [{label, amount}], cost, revenue, profit, roi, breakEvenTons}
    """
    acres = acres or 1.0
    crop_key = (crop or "").strip().lower()

    seed_rate = season_plan.get("seed_rate_kg_per_acre") or 0
    seed_price = SEED_PRICE_BDT_PER_KG.get(crop_key, DEFAULT_SEED_PRICE_BDT_PER_KG)
    seed_cost = round(seed_rate * seed_price * acres)

    fertilizer_cost_per_acre = sum(
        (item.get("amount_kg_per_acre") or 0) * _fertilizer_price(item.get("name", ""))
        for item in (season_plan.get("fertilizer_schedule") or [])
    )
    fertilizer_cost = round(fertilizer_cost_per_acre * acres)

    land_prep_cost = round(LAND_PREP_COST_BDT_PER_ACRE * acres)
    irrigation_cost = round(IRRIGATION_COST_BDT_PER_ACRE * acres)
    pest_cost = round(PEST_CONTROL_COST_BDT_PER_ACRE * acres)
    labor_cost = round(LABOR_COST_BDT_PER_ACRE * acres)
    post_harvest_cost = round(POST_HARVEST_COST_BDT_PER_ACRE * acres)

    items = [
        {"label": "Land Preparation", "amount": land_prep_cost},
        {"label": "Seeds", "amount": seed_cost},
        {"label": "Fertilizer", "amount": fertilizer_cost},
        {"label": "Irrigation", "amount": irrigation_cost},
        {"label": "Pest & Disease Control", "amount": pest_cost},
        {"label": "Labor", "amount": labor_cost},
        {"label": "Post-harvest & Transport", "amount": post_harvest_cost},
    ]
    total_cost = sum(item["amount"] for item in items)

    market_price = MARKET_PRICE_BDT_PER_TON.get(crop_key, DEFAULT_MARKET_PRICE_BDT_PER_TON)
    expected_yield = season_plan.get("expected_yield_ton_per_acre") or 0
    revenue = round(expected_yield * acres * market_price)
    profit = revenue - total_cost
    roi = round((profit / total_cost) * 100) if total_cost else 0
    break_even_tons = round(total_cost / market_price, 2) if market_price else 0

    return {
        "items": items,
        "cost": total_cost,
        "revenue": revenue,
        "profit": profit,
        "roi": roi,
        "breakEvenTons": break_even_tons,
        "market_price_bdt_per_ton": market_price,
    }


def apply_budget_constraint(season_plan: dict, crop: str, acres: float, new_budget: float) -> dict:
    """Returns a deep copy of `season_plan` with fertilizer quantities scaled
    down (never up) just enough to fit `new_budget`, or an unmodified copy if
    the plan already fits within it.

    Fertilizer is the one elastic, schedule-driven cost line — land prep,
    seed, irrigation, pest control, labor, and post-harvest are treated as
    fixed per-acre costs a farmer can't meaningfully shrink turn-by-turn.
    This is what `scenario_handler` calls when the farmer asks to actually
    apply a budget scenario, not just hear about the shortfall.
    """

    baseline = calculate_financials(season_plan, crop, acres)
    if baseline["cost"] <= new_budget:
        return copy.deepcopy(season_plan)

    fertilizer_item = next(item for item in baseline["items"] if item["label"] == "Fertilizer")
    fixed_cost = baseline["cost"] - fertilizer_item["amount"]
    if fertilizer_item["amount"] <= 0:
        # Nothing elastic left to cut — can't fit this budget by scaling
        # fertilizer alone.
        return copy.deepcopy(season_plan)

    scale = max(0.0, min(1.0, (new_budget - fixed_cost) / fertilizer_item["amount"]))

    adjusted = copy.deepcopy(season_plan)
    for item in adjusted.get("fertilizer_schedule", []):
        old_amount = item["amount_kg_per_acre"]
        new_amount = round(old_amount * scale, 2)
        if new_amount != old_amount:
            item["amount_kg_per_acre"] = new_amount
            item["adjusted"] = True
            item["adjustment_note"] = (
                f"Reduced from {old_amount} to {new_amount} kg/acre to fit a tighter budget."
            )
    return adjusted
