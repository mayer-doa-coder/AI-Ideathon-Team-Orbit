"""supervisor_router is a pure function over AgentState — no DB/LLM calls —
so each branch of the decision table (architecture.md §7) is directly
testable with a minimal state dict."""
from app.agents.router import supervisor_router


def _state(**overrides):
    base = {
        "turn_complete": False,
        "intent": None,
        "season_plan": None,
        "missing_fields": [],
        "weather_data": {"dates": ["2026-01-01"]},
        "crop_candidates": [{"id": "rice"}],
        "selected_crop": None,
    }
    base.update(overrides)
    return base


def test_turn_complete_always_ends_regardless_of_intent():
    assert supervisor_router(_state(turn_complete=True, intent="slot_fill")) == "end"


def test_chitchat_routes_to_casual_response():
    assert supervisor_router(_state(intent="chitchat")) == "casual_response"


def test_off_topic_routes_to_off_topic_redirect():
    assert supervisor_router(_state(intent="off_topic")) == "off_topic_redirect"


def test_agro_question_routes_to_qa_agent():
    assert supervisor_router(_state(intent="agro_question")) == "qa_agent"


def test_scenario_with_existing_plan_routes_to_scenario_handler():
    state = _state(intent="scenario", season_plan={"crop": "Rice"})
    assert supervisor_router(state) == "scenario_handler"


def test_scenario_without_plan_routes_to_scenario_blocked():
    assert supervisor_router(_state(intent="scenario", season_plan=None)) == "scenario_blocked"


def test_slot_fill_with_committed_plan_ends_turn():
    state = _state(intent="slot_fill", season_plan={"crop": "Rice"})
    assert supervisor_router(state) == "end"


def test_slot_fill_with_missing_fields_asks_followup():
    state = _state(intent="slot_fill", missing_fields=["soil_type"])
    assert supervisor_router(state) == "ask_followup"


def test_slot_fill_without_weather_but_with_candidates_calls_weather_tool():
    # Candidates already exist, so only the forecast is missing — the
    # standalone weather node handles that and re-enters the router. No
    # retrieval or re-ranking is needed, so this must NOT fan out.
    state = _state(intent="slot_fill", weather_data=None)
    assert supervisor_router(state) == "weather_tool"


def test_slot_fill_without_crop_candidates_fans_out_to_gather_context():
    # Crop candidates need both a forecast and retrieved agronomy, which are
    # independent — the router sends this to the fan-out so weather_parallel
    # and knowledge_retrieval run concurrently and join at
    # crop_recommendation. crop_recommendation is deliberately unreachable
    # from the router now; entering it directly would rank crops against an
    # empty knowledge context. See nodes/gather_context.py.
    state = _state(intent="slot_fill", crop_candidates=[])
    assert supervisor_router(state) == "gather_context"


def test_slot_fill_missing_both_weather_and_candidates_fans_out_once():
    # The pre-parallel graph took two router passes here (weather_tool, then
    # crop_recommendation). One fan-out now covers both.
    state = _state(intent="slot_fill", weather_data=None, crop_candidates=[])
    assert supervisor_router(state) == "gather_context"


def test_slot_fill_with_selected_crop_calls_season_planner():
    state = _state(intent="slot_fill", selected_crop="Rice")
    assert supervisor_router(state) == "season_planner"


def test_slot_fill_fallback_ends_when_nothing_left_to_do():
    # All prerequisites satisfied but no crop selected yet — nothing left
    # for the router to trigger this turn; it waits for the farmer's pick.
    state = _state(intent="slot_fill", selected_crop=None)
    assert supervisor_router(state) == "end"


def test_pending_replan_confirmation_takes_priority_over_intent():
    # A bare "yes"/"no" could easily get misclassified as chitchat — this
    # must win regardless of what intent classify_intent settled on.
    state = _state(intent="chitchat", pending_replan_confirmation=True)
    assert supervisor_router(state) == "core_change_handler"


def test_core_field_change_with_existing_plan_routes_to_core_change_handler():
    state = _state(
        intent="slot_fill",
        season_plan={"crop": "Rice"},
        farm_profile={"location": "Khulna"},
        committed_farm_profile={"location": "Rajshahi"},
    )
    assert supervisor_router(state) == "core_change_handler"


def test_core_field_change_before_anything_computed_is_normal_slot_fill():
    # Nothing has been computed from the old value yet (no weather, no
    # candidates, no plan) — this is genuinely just regular onboarding
    # correcting a field, not a mid-conversation change to walk back.
    state = _state(
        intent="slot_fill",
        season_plan=None,
        missing_fields=[],
        weather_data=None,
        crop_candidates=[],
        farm_profile={"location": "Khulna"},
        committed_farm_profile={"location": "Rajshahi"},
    )
    assert supervisor_router(state) != "core_change_handler"


def test_core_field_change_after_candidates_but_before_plan_routes_to_core_change_handler():
    # Weather/candidates were already fetched for the old location, but no
    # plan is committed yet. Silently falling through here (the pre-fix
    # behavior) left the farmer with stale, wrong-location recommendations
    # and zero acknowledgment that anything happened.
    state = _state(
        intent="slot_fill",
        season_plan=None,
        missing_fields=[],
        farm_profile={"location": "Khulna"},
        committed_farm_profile={"location": "Rajshahi"},
    )
    assert supervisor_router(state) == "core_change_handler"


def test_first_time_profile_completion_never_routes_to_core_change_handler():
    # A brand-new farmer has no Farm row in Postgres yet, so
    # committed_farm_profile is still {} the whole time they're being
    # onboarded — every field they state for the first time must NOT read
    # as a "change from None". This is the exact bug: the turn that
    # completes the profile also runs weather_tool, which makes the guard's
    # weather_data/crop_candidates check truthy for the first time, and
    # committed_farm_profile being {} used to make _core_field_changed
    # misfire right at that moment, before any plan had ever existed.
    state = _state(
        intent="slot_fill",
        season_plan=None,
        missing_fields=[],
        farm_profile={
            "location": "Dhaka",
            "soil_type": "clay",
            "water_availability": "low",
            "season": "summer",
        },
        committed_farm_profile={},
    )
    assert supervisor_router(state) != "core_change_handler"


def test_acres_or_budget_change_never_routes_to_core_change_handler():
    # Acres/budget are deliberately excluded from CORE_REPLAN_FIELDS —
    # scenario_handler already owns replanning the same crop for those.
    state = _state(
        intent="slot_fill",
        season_plan={"crop": "Rice"},
        farm_profile={"acres": 5.0, "budget": 90000.0},
        committed_farm_profile={"acres": 2.0, "budget": 30000.0},
    )
    assert supervisor_router(state) != "core_change_handler"


def test_unchanged_core_fields_do_not_trigger_core_change_handler():
    state = _state(
        intent="slot_fill",
        season_plan={"crop": "Rice"},
        farm_profile={"location": "Rajshahi"},
        committed_farm_profile={"location": "Rajshahi"},
    )
    assert supervisor_router(state) == "end"
