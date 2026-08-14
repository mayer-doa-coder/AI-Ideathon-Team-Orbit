"""Handles a farm's *core identity* changing mid-conversation — location,
soil type, water availability, or season (`CORE_REPLAN_FIELDS`) — as
opposed to `scenario_handler`, which owns budget/area/input changes to an
existing plan. The distinction matters: a budget cut can be absorbed by
replanning the *same* crop, but a location change can invalidate which
crop even makes sense, so it needs a different kind of confirmation.

Two situations land here:

1. The farmer just stated a new core fact after weather, crop candidates,
   or a full plan were already computed from the *old* value — see
   `router.py`'s trigger condition (`_handle_core_change`). This commits it
   to Postgres immediately — the
   dashboard reflects it right away, it doesn't wait for the farmer to
   confirm anything — then asks whether to rebuild the crop recommendation
   and season plan around it. Silently keeping the old crop/plan after a
   location change would be actively wrong (grounded in the wrong
   weather); silently discarding it would ignore a farmer who only meant
   to fix a typo.
2. The farmer is answering that question (`_handle_confirmation`). Yes
   clears crop_candidates/selected_crop/season_plan/financials/weather —
   and, if location changed, the stale lat/lon too, so `weather_tool` is
   forced to re-geocode rather than fetch weather for the old place under
   the new name — and hands off to the router's existing slot_fill chain
   to rebuild from weather_tool onward. No leaves everything else exactly
   as committed.
"""
from langchain_core.messages import AIMessage

from app.agents.state import CORE_REPLAN_FIELDS, REQUIRED_FARM_FIELDS, AgentState
from app.db.models import Farm
from app.db.session import SessionLocal

FIELD_LABELS = {
    "location": "location",
    "soil_type": "soil type",
    "water_availability": "water availability",
    "season": "season",
}


def _commit_farm_profile(farmer_id: str, farm_profile: dict, clear_coordinates: bool) -> None:
    db = SessionLocal()
    try:
        farm = db.query(Farm).filter(Farm.user_id == int(farmer_id)).first()
        if not farm:
            return
        for field in [*REQUIRED_FARM_FIELDS, "lat", "lon"]:
            if field in farm_profile:
                setattr(farm, field, farm_profile[field])
        if clear_coordinates:
            # The old lat/lon belong to the old location — leaving them in
            # place would make weather_tool skip re-geocoding (it only acts
            # when lat/lon are *missing*, not merely stale) and fetch
            # weather for the wrong place under the new location's name.
            farm.lat = None
            farm.lon = None
        db.commit()
    finally:
        db.close()


def _changed_core_fields(state: AgentState) -> list[str]:
    farm_profile = state.get("farm_profile") or {}
    committed = state.get("committed_farm_profile") or {}
    # Same guard as router.py's _core_field_changed: only count it as a
    # change if there was a real prior committed value — otherwise a
    # brand-new farmer's first-ever profile reads as "everything changed".
    return [
        f
        for f in CORE_REPLAN_FIELDS
        if committed.get(f) is not None
        and farm_profile.get(f) is not None
        and farm_profile.get(f) != committed.get(f)
    ]


def core_change_handler(state: AgentState) -> dict:
    if state.get("pending_replan_confirmation"):
        return _handle_confirmation(state)
    return _handle_core_change(state)


def _handle_core_change(state: AgentState) -> dict:
    farm_profile = state.get("farm_profile") or {}
    committed = state.get("committed_farm_profile") or {}
    changed = _changed_core_fields(state)

    _commit_farm_profile(
        state["farmer_id"], farm_profile, clear_coordinates="location" in changed
    )

    # Name the actual old -> new values, not just which fields changed —
    # "changed your location" leaves the farmer to go check the dashboard
    # to confirm what actually happened; naming it is the whole point of
    # a confirmation message.
    change_descriptions = []
    for f in changed:
        old_value = committed.get(f)
        new_value = farm_profile.get(f)
        label = FIELD_LABELS.get(f, f)
        if old_value is not None:
            change_descriptions.append(f"{label} from {old_value} to {new_value}")
        else:
            change_descriptions.append(f"{label} to {new_value}")
    changed_text = " and ".join(change_descriptions) or "your profile"
    text = (
        f"Okay, I've changed the {changed_text}. Since that changes what actually suits this "
        f"farm, would you like me to work out a completely new crop recommendation and season "
        f"plan for it? (yes/no)"
    )

    return {
        "pending_replan_confirmation": True,
        "pending_replan_fields": changed,
        "turn_complete": True,
        "messages": [AIMessage(content=text)],
    }


def _handle_confirmation(state: AgentState) -> dict:
    confirms = state.get("confirms_pending_replan")
    fields = state.get("pending_replan_fields") or []
    changed_text = " and ".join(FIELD_LABELS.get(f, f) for f in fields) or "your profile"

    if confirms is None:
        # Couldn't tell yes/no from that reply — ask again plainly rather
        # than guess and silently do (or not do) something the farmer
        # didn't actually ask for.
        return {
            "pending_replan_confirmation": True,
            "pending_replan_fields": fields,
            "turn_complete": True,
            "messages": [
                AIMessage(
                    content="Sorry, just to confirm — yes or no, should I build a new plan for this?"
                )
            ],
        }

    if confirms:
        farm_profile = dict(state.get("farm_profile") or {})
        if "location" in fields:
            farm_profile.pop("lat", None)
            farm_profile.pop("lon", None)
        return {
            "farm_profile": farm_profile,
            "pending_replan_confirmation": False,
            "pending_replan_fields": [],
            "weather_data": None,
            "crop_candidates": [],
            "selected_crop": None,
            "season_plan": None,
            "financials": None,
            # Tells load_memory to stop resyncing crop_candidates/selected_
            # crop/season_plan/financials from Postgres on every future turn
            # until persist commits the new plan — otherwise the *previous*
            # committed plan (still sitting in Postgres) would silently
            # overwrite these fresh candidates the moment the farmer picks
            # one, on the very next turn.
            "replanning": True,
            # Not complete — let the router continue straight into
            # weather_tool -> crop_recommendation in this same turn, the
            # same chain a fresh onboarding uses.
            "turn_complete": False,
            "messages": [AIMessage(content=f"Great — let's rebuild your plan for the updated {changed_text}.")],
        }

    return {
        "pending_replan_confirmation": False,
        "pending_replan_fields": [],
        "turn_complete": True,
        "messages": [AIMessage(content="No problem — kept your existing crop and season plan as is.")],
    }
