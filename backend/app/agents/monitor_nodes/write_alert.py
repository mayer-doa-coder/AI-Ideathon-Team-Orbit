"""Terminal node: persists the alert and — critically — writes the
recomputed plan/financials back into the farm's committed `plans` row.

That last part is what makes the adjustment "memory" rather than a one-off
notification: without it, every future sweep would keep re-discovering the
same stale, un-adjusted schedule and re-trigger forever.
"""
from app.agents.monitor_nodes.compare_thresholds import RUNOFF_DELAY_DAYS
from app.agents.state import MonitorState
from app.db.models import Alert, Plan
from app.db.session import SessionLocal
from app.db.trace import log_trace


def _build_message(state: MonitorState) -> str:
    ctx = state["trigger_context"]
    if ctx["type"] == "runoff_risk":
        return (
            f"Heavy rain forecast ({ctx['rain_mm']:.0f}mm) near your {ctx['item_name']} "
            f"application on {ctx['item_date']}. Delayed it by {RUNOFF_DELAY_DAYS} days "
            f"to cut nutrient runoff loss."
        )
    return (
        f"{ctx['rain_mm']:.0f}mm rain forecast in the next few days — conditions now favor "
        f"{ctx['item_name']}. Added a preventive treatment to your plan."
    )


def write_alert(state: MonitorState) -> dict:
    if not state.get("triggered"):
        return {}

    message = _build_message(state)

    db = SessionLocal()
    try:
        alert = Alert(
            farm_id=state["farm_id"],
            trigger_reason=state["trigger_reason"],
            message=message,
            payload={
                "updated_plan": state.get("updated_plan"),
                "updated_financials": state.get("updated_financials"),
            },
        )
        db.add(alert)

        plan_row = db.query(Plan).filter(Plan.farm_id == state["farm_id"]).one_or_none()
        if plan_row is not None:
            if state.get("updated_plan"):
                plan_row.season_plan = state["updated_plan"]
            if state.get("updated_financials"):
                plan_row.financials = state["updated_financials"]

        db.commit()
        db.refresh(alert)
        alert_id = alert.id
    finally:
        db.close()

    log_trace(
        farm_id=state["farm_id"], source="monitor", node_name="write_alert",
        params={"trigger_reason": state["trigger_reason"]},
        result={"alert_id": alert_id, "plan_updated": bool(state.get("updated_plan"))},
    )
    return {}
