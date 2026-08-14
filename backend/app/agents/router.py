"""supervisor_router — the conversation graph's conditional-edge decision
function. Invoked after classify_intent, again after weather_tool, and
again after core_change_handler (the three nodes that can continue the
turn instead of ending it).

intake_router — invoked once, right after load_memory, before intent
classification even runs. A photo attached to the turn always means disease
detection, regardless of what (if anything) the farmer typed alongside it,
so this bypasses classify_intent entirely rather than adding "has_image" as
another branch of supervisor_router's intent-based routing. Voice audio
gets the same treatment via voice_input, except that node's whole job is to
turn itself into a normal typed message and hand off to classify_intent —
see voice_input_router below.

voice_input_router — invoked once, right after voice_input. On a successful
transcription this rejoins the exact same intake path a typed message
takes (classify_intent), so none of the downstream agent logic needs a
voice-specific branch. On a failed transcription voice_input has already
ended the turn with an explanation message, so this instead heads straight
to voice_output (state.voice_input.used is still true, so the farmer still
gets that explanation read back to them)."""
from app.agents.state import CORE_REPLAN_FIELDS, AgentState


def _core_field_changed(state: AgentState) -> bool:
    farm_profile = state.get("farm_profile") or {}
    committed = state.get("committed_farm_profile") or {}
    # committed.get(f) is not None guards against the pre-persistence
    # window: `committed_farm_profile` only reflects Postgres, and no Farm
    # row exists there until a plan is first persisted, so it's `{}` for a
    # brand-new farmer's whole onboarding. Without this check, every field
    # being stated for the first time reads as "changed from None" and
    # falsely triggers a replan confirmation before a plan has ever existed.
    return any(
        committed.get(f) is not None
        and farm_profile.get(f) is not None
        and farm_profile.get(f) != committed.get(f)
        for f in CORE_REPLAN_FIELDS
    )


def intake_router(state: AgentState) -> str:
    if state.get("uploaded_image"):
        return "disease_detection"
    if state.get("uploaded_audio"):
        return "voice_input"
    return "classify_intent"


def voice_input_router(state: AgentState) -> str:
    if (state.get("voice_input") or {}).get("transcribed_text"):
        return "classify_intent"
    return "voice_output"


def supervisor_router(state: AgentState) -> str:
    if state.get("turn_complete"):
        return "end"

    # Highest priority, regardless of classified intent: a bare "yes"/"no"
    # answering the pending replan question can easily get misclassified
    # as chitchat on its own, so this has to short-circuit before the
    # normal intent branches even look at it.
    if state.get("pending_replan_confirmation"):
        return "core_change_handler"

    # Also high priority: a farm fact that actually invalidates crop
    # suitability (location/soil/water/season) matters more than whatever
    # else the message also said. Fires once anything has already been
    # computed from the *old* value of that fact — weather, candidates, or
    # a full plan — since all three would now silently be wrong for the new
    # one. Without this, the fall-through slot-fill chain below sees
    # weather_data/crop_candidates already truthy (from the old profile)
    # and treats them as "nothing to do", ending the turn with the profile
    # quietly updated but no acknowledgment and stale recommendations left
    # on screen. During initial onboarding (none of these exist yet) this
    # is still just normal slot-filling, so it stays a no-op there.
    if (
        state.get("weather_data") or state.get("crop_candidates") or state.get("season_plan")
    ) and _core_field_changed(state):
        return "core_change_handler"

    intent = state.get("intent")

    if intent == "chitchat":
        return "casual_response"
    if intent == "off_topic":
        return "off_topic_redirect"
    if intent == "agro_question":
        return "qa_agent"
    if intent == "scenario":
        return "scenario_handler" if state.get("season_plan") else "scenario_blocked"
    if intent == "marketplace":
        return "marketplace_lookup"
    if intent == "market_price":
        return "market_price_lookup"

    # intent == "slot_fill" (default/fallback)
    if state.get("season_plan"):
        return "end"
    if state.get("missing_fields"):
        return "ask_followup"

    # Crop candidates need two independent inputs — a forecast and retrieved
    # agronomy — so route to the fan-out, which runs both concurrently and
    # joins into crop_recommendation. This replaces what used to be two
    # sequential router passes (weather_tool, then crop_recommendation) and is
    # the single biggest latency win in the turn. weather_tool no-ops if a
    # forecast is already in state, so entering here with one is cheap.
    # See nodes/gather_context.py.
    if not state.get("crop_candidates"):
        return "gather_context"

    # Candidates already exist and only the forecast is missing (e.g. it was
    # invalidated on its own): the standalone weather node handles that and
    # re-enters this router, with no retrieval or re-ranking needed.
    if not state.get("weather_data"):
        return "weather_tool"

    if state.get("selected_crop"):
        return "season_planner"
    return "end"
