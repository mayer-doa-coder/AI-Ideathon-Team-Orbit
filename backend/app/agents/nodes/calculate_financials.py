from app.agents.state import AgentState
from app.tools.financials import calculate_financials as compute_financials


def calculate_financials(state: AgentState) -> dict:
    season_plan = state.get("season_plan") or {}
    crop = state.get("selected_crop") or ""
    acres = (state.get("farm_profile") or {}).get("acres") or 1.0

    financials = compute_financials(season_plan, crop, acres)

    trace = [
        {
            "type": "financial",
            "tool": "calculate_financials",
            "paramsDisplay": f'crop="{crop}", acres={acres}',
            "params": {
                "crop": crop,
                "acres": acres,
                "seed_rate_kg_per_acre": season_plan.get("seed_rate_kg_per_acre"),
                "expected_yield_ton_per_acre": season_plan.get("expected_yield_ton_per_acre"),
            },
            "response": financials,
            "summary": (
                f"cost ৳{financials['cost']:,}, revenue ৳{financials['revenue']:,}, "
                f"profit ৳{financials['profit']:,}, ROI {financials['roi']}%"
            ),
        }
    ]

    return {"financials": financials, "trace_log": trace}
