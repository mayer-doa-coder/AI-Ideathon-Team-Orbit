"""Re-costs the plan with the shared `tools/financials.calculate_financials`
— the same function the conversation graph uses — so a monitor adjustment
(e.g. a delayed fertilizer application) shows up as a real, inspectable
change to the exact cost breakdown the farmer already sees in the dashboard,
in the same shape, not a second incompatible set of numbers.
"""
from app.agents.state import MonitorState
from app.db.trace import log_trace
from app.tools.financials import calculate_financials


def recompute_financials(state: MonitorState) -> dict:
    if not state.get("triggered") or not state.get("updated_plan"):
        return {"updated_financials": None}

    farm = state["farm"]
    updated_plan = state["updated_plan"]
    crop = updated_plan["crop"]
    financials = calculate_financials(updated_plan, crop, farm["acres"])

    log_trace(
        farm_id=state["farm_id"], source="monitor", node_name="recompute_financials",
        tool_name="calculate_financials",
        params={"crop": crop, "acres": farm["acres"]},
        result={"total_cost": financials["cost"], "net_profit": financials["profit"]},
    )
    return {"updated_financials": financials}
