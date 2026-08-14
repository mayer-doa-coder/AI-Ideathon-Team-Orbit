from app.agents.state import REQUIRED_FARM_FIELDS, AgentState
from app.db.models import Farm, Plan
from app.db.session import SessionLocal


def load_memory(state: AgentState) -> dict:
    """Entry point. Hydrates farm_profile/selected_crop/season_plan/financials
    from the durable domain tables on *every* turn, not just a thread's first
    one. This has to run every turn (not only when the checkpointer has no
    state yet) because `plans` isn't only written by this graph's own
    `persist` node — the monitor graph adjusts `season_plan`/`financials` in
    place directly in Postgres (see `monitor_nodes/write_alert.py`) whenever
    it fires between chat turns. If this node only hydrated a cold thread,
    the chat/dashboard view of a farm would go stale the moment the monitor
    made its first adjustment, and a later `scenario_handler` call would
    simulate against the pre-adjustment plan.

    Exception: while `state["replanning"]` is true (a core-field change was
    confirmed and a fresh crop_recommendation/season_planner run is under
    way but hasn't reached `persist` yet), the *committed* row in Postgres
    still holds the previous plan — resyncing from it here would silently
    overwrite the freshly generated, not-yet-committed candidates with
    stale data before the farmer even gets to pick from them. So
    selected_crop/crop_candidates/season_plan/financials are skipped for
    that window; farm_profile itself is still always resynced, since that
    part IS already durably committed by `core_change_handler`."""
    user_id = int(state["farmer_id"])
    db = SessionLocal()
    try:
        farm = db.query(Farm).filter(Farm.user_id == user_id).first()
        if not farm:
            return {}

        farm_profile = {
            k: v
            for k, v in {
                "location": farm.location,
                "lat": farm.lat,
                "lon": farm.lon,
                "acres": farm.acres,
                "soil_type": farm.soil_type,
                "water_availability": farm.water_availability,
                "budget": farm.budget,
                "season": farm.season,
            }.items()
            if v is not None
        }
        missing = [f for f in REQUIRED_FARM_FIELDS if f not in farm_profile]
        # A separate copy, not the same dict object — classify_intent merges
        # newly-extracted fields into `farm_profile` this same turn, and
        # `core_change_handler` needs this untouched snapshot to diff
        # against to see what actually changed.
        update: dict = {
            "farm_profile": farm_profile,
            "committed_farm_profile": dict(farm_profile),
            "missing_fields": missing,
        }

        if not state.get("replanning"):
            plan = db.query(Plan).filter(Plan.farm_id == farm.id).first()
            if plan:
                update["selected_crop"] = plan.selected_crop
                update["crop_candidates"] = plan.crop_candidates or []
                update["season_plan"] = plan.season_plan
                update["financials"] = plan.financials

        return update
    finally:
        db.close()
