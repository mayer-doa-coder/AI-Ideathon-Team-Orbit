from app.tools.financials import apply_budget_constraint, calculate_financials


def _season_plan(seed_rate=10, fert_kg=50, yield_ton=1.5):
    return {
        "seed_rate_kg_per_acre": seed_rate,
        "fertilizer_schedule": [{"name": "urea", "amount_kg_per_acre": fert_kg}],
        "expected_yield_ton_per_acre": yield_ton,
    }


def test_items_sum_to_total_cost():
    result = calculate_financials(_season_plan(), "rice", acres=2)
    assert sum(item["amount"] for item in result["items"]) == result["cost"]


def test_profit_is_revenue_minus_cost():
    result = calculate_financials(_season_plan(), "rice", acres=2)
    assert result["profit"] == result["revenue"] - result["cost"]


def test_scaling_acres_scales_cost_and_revenue():
    one_acre = calculate_financials(_season_plan(), "rice", acres=1)
    two_acres = calculate_financials(_season_plan(), "rice", acres=2)
    assert two_acres["cost"] == 2 * one_acre["cost"]
    assert two_acres["revenue"] == 2 * one_acre["revenue"]


def test_higher_yield_increases_revenue_and_profit():
    low = calculate_financials(_season_plan(yield_ton=1.0), "rice", acres=1)
    high = calculate_financials(_season_plan(yield_ton=2.0), "rice", acres=1)
    assert high["revenue"] > low["revenue"]
    assert high["profit"] > low["profit"]


def test_unknown_crop_falls_back_to_default_price_without_erroring():
    result = calculate_financials(_season_plan(), "unobtainium", acres=1)
    assert result["revenue"] > 0


def test_fertilizer_line_item_reflects_the_schedule():
    # Regression guard: `fertilizer_schedule` items key their quantity as
    # `amount_kg_per_acre` (matching the shared SeasonPlan shape both the
    # conversation and monitor graphs use) — a stale/wrong key here would
    # silently zero out the fertilizer cost line instead of raising.
    zero_fert = calculate_financials(_season_plan(fert_kg=0), "rice", acres=1)
    with_fert = calculate_financials(_season_plan(fert_kg=100), "rice", acres=1)
    fert_item = next(item for item in with_fert["items"] if item["label"] == "Fertilizer")
    assert fert_item["amount"] > 0
    assert with_fert["cost"] > zero_fert["cost"]


def test_apply_budget_constraint_no_change_when_already_within_budget():
    plan = _season_plan(fert_kg=50)
    baseline_cost = calculate_financials(plan, "rice", acres=1)["cost"]
    adjusted = apply_budget_constraint(plan, "rice", acres=1, new_budget=baseline_cost + 10000)
    assert adjusted["fertilizer_schedule"][0]["amount_kg_per_acre"] == 50
    assert "adjusted" not in adjusted["fertilizer_schedule"][0]


def test_apply_budget_constraint_scales_fertilizer_down_to_fit():
    plan = _season_plan(fert_kg=100)
    baseline = calculate_financials(plan, "rice", acres=1)
    tight_budget = baseline["cost"] - 500  # force a real shortfall

    adjusted = apply_budget_constraint(plan, "rice", acres=1, new_budget=tight_budget)
    new_cost = calculate_financials(adjusted, "rice", acres=1)["cost"]

    assert adjusted["fertilizer_schedule"][0]["amount_kg_per_acre"] < 100
    assert adjusted["fertilizer_schedule"][0]["adjusted"] is True
    assert new_cost <= tight_budget + 1  # +1 for rounding


def test_apply_budget_constraint_never_scales_fertilizer_up():
    plan = _season_plan(fert_kg=50)
    baseline_cost = calculate_financials(plan, "rice", acres=1)["cost"]
    # A much larger budget shouldn't inflate input quantities — only a
    # tighter budget scales anything, per the function's own contract.
    adjusted = apply_budget_constraint(plan, "rice", acres=1, new_budget=baseline_cost * 10)
    assert adjusted["fertilizer_schedule"][0]["amount_kg_per_acre"] == 50


def test_apply_budget_constraint_floors_at_zero_not_negative():
    plan = _season_plan(fert_kg=50)
    adjusted = apply_budget_constraint(plan, "rice", acres=1, new_budget=1)
    assert adjusted["fertilizer_schedule"][0]["amount_kg_per_acre"] >= 0


def test_fertilizer_price_matches_descriptive_llm_names_not_just_exact_tags():
    # Regression guard: the LLM writes names like "Well-decomposed cowdung"
    # or "Urea (1st split - basal)", not the bare "cowdung"/"urea" tags the
    # price table is keyed by. An exact-match lookup silently fell back to
    # the (much higher) default price for these, badly overcharging common
    # low-cost items like cowdung by ~10x.
    def _plan_with(name):
        return {
            "seed_rate_kg_per_acre": 0,
            "fertilizer_schedule": [{"name": name, "amount_kg_per_acre": 100}],
            "expected_yield_ton_per_acre": 1.0,
        }

    exact = calculate_financials(_plan_with("cowdung"), "rice", acres=1)
    descriptive = calculate_financials(_plan_with("Well-decomposed cowdung"), "rice", acres=1)
    assert exact["cost"] == descriptive["cost"]
