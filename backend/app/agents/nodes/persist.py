from langchain_core.messages import AIMessage

from app.agents.state import REQUIRED_FARM_FIELDS, AgentState
from app.db.models import Farm, Plan
from app.db.session import SessionLocal


def _build_summary_message(state: AgentState) -> str:
    crop = state.get("selected_crop") or "your crop"
    plan = state.get("season_plan") or {}
    fin = state.get("financials") or {}

    lines = [f"Here's your season plan for {crop}:"]
    sowing = plan.get("sowing_window") or {}
    harvest = plan.get("harvest_window") or {}
    if sowing:
        harvest_text = (
            f"{harvest['start']} to {harvest['end']}" if harvest else "in due course"
        )
        lines.append(f"Sow {sowing['start']} to {sowing['end']}, harvest {harvest_text}.")
    if fin:
        lines.append(
            f"Estimated cost ৳{fin['cost']:,}, revenue ৳{fin['revenue']:,}, "
            f"net profit ৳{fin['profit']:,} (ROI {fin['roi']}%, break-even at {fin['breakEvenTons']} tons)."
        )
    lines.append("Full details, reasoning, and sources are in the panel on the right.")
    return "\n".join(lines)


def persist(state: AgentState) -> dict:
    """Writes the committed farm profile + plan to the durable domain tables.
    Scenario runs never overwrite the committed plan."""
    user_id = int(state["farmer_id"])
    db = SessionLocal()
    try:
        farm = db.query(Farm).filter(Farm.user_id == user_id).first()
        if not farm:
            farm = Farm(user_id=user_id)
            db.add(farm)

        profile = state.get("farm_profile") or {}
        for field in [*REQUIRED_FARM_FIELDS, "lat", "lon"]:
            if field in profile:
                setattr(farm, field, profile[field])
        db.flush()

        if not state.get("is_scenario") and state.get("season_plan"):
            plan = db.query(Plan).filter(Plan.farm_id == farm.id).first()
            if not plan:
                plan = Plan(farm_id=farm.id)
                db.add(plan)
            plan.selected_crop = state.get("selected_crop")
            plan.crop_candidates = state.get("crop_candidates") or []
            plan.season_plan = state.get("season_plan")
            plan.financials = state.get("financials")

        db.commit()
    finally:
        db.close()

    return {
        "turn_complete": True,
        # Safe to always include: this only ever matters when a core-change
        # replan was actually in progress (see load_memory's docstring),
        # and is a harmless no-op otherwise since it's already False.
        "replanning": False,
        "messages": [AIMessage(content=_build_summary_message(state))],
    }
