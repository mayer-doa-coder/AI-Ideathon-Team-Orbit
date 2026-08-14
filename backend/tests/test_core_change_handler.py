from app.agents.nodes.core_change_handler import _changed_core_fields, _handle_confirmation


def _state(**overrides):
    base = {
        "farmer_id": "1",
        "farm_profile": {},
        "committed_farm_profile": {},
        "pending_replan_fields": [],
        "confirms_pending_replan": None,
    }
    base.update(overrides)
    return base


def test_changed_core_fields_detects_a_real_change():
    state = _state(
        farm_profile={"location": "Khulna", "acres": 2.0},
        committed_farm_profile={"location": "Rajshahi", "acres": 2.0},
    )
    assert _changed_core_fields(state) == ["location"]


def test_changed_core_fields_ignores_acres_and_budget():
    state = _state(
        farm_profile={"acres": 5.0, "budget": 90000.0},
        committed_farm_profile={"acres": 2.0, "budget": 30000.0},
    )
    assert _changed_core_fields(state) == []


def test_changed_core_fields_ignores_unset_fields():
    # A field that's simply absent from farm_profile isn't a "change" —
    # only an actually-different, present value counts.
    state = _state(
        farm_profile={"location": None},
        committed_farm_profile={"location": "Rajshahi"},
    )
    assert _changed_core_fields(state) == []


def test_changed_core_fields_can_detect_multiple():
    state = _state(
        farm_profile={"location": "Khulna", "season": "Winter"},
        committed_farm_profile={"location": "Rajshahi", "season": "Summer"},
    )
    assert set(_changed_core_fields(state)) == {"location", "season"}


def test_handle_confirmation_yes_clears_plan_and_continues_turn():
    state = _state(
        pending_replan_confirmation=True,
        confirms_pending_replan=True,
        pending_replan_fields=["location"],
        farm_profile={"location": "Khulna", "lat": 24.1, "lon": 90.1},
    )
    result = _handle_confirmation(state)

    assert result["turn_complete"] is False
    assert result["season_plan"] is None
    assert result["crop_candidates"] == []
    assert result["selected_crop"] is None
    assert result["financials"] is None
    assert result["weather_data"] is None
    assert result["pending_replan_confirmation"] is False
    # lat/lon must be dropped so weather_tool is forced to re-geocode
    # instead of fetching weather for the old coordinates.
    assert "lat" not in result["farm_profile"]
    assert "lon" not in result["farm_profile"]


def test_handle_confirmation_yes_keeps_coordinates_when_location_unchanged():
    # Only clear lat/lon when location itself was part of what changed —
    # a soil-type-only change has no reason to force a re-geocode.
    state = _state(
        pending_replan_confirmation=True,
        confirms_pending_replan=True,
        pending_replan_fields=["soil_type"],
        farm_profile={"location": "Rajshahi", "lat": 24.1, "lon": 90.1, "soil_type": "Clay"},
    )
    result = _handle_confirmation(state)
    assert result["farm_profile"]["lat"] == 24.1
    assert result["farm_profile"]["lon"] == 90.1


def test_handle_confirmation_no_ends_turn_and_keeps_plan_untouched():
    state = _state(
        pending_replan_confirmation=True,
        confirms_pending_replan=False,
        pending_replan_fields=["location"],
    )
    result = _handle_confirmation(state)

    assert result["turn_complete"] is True
    assert result["pending_replan_confirmation"] is False
    assert "season_plan" not in result  # untouched, not reset to None
    assert "crop_candidates" not in result


def test_handle_confirmation_unclear_asks_again():
    state = _state(
        pending_replan_confirmation=True,
        confirms_pending_replan=None,
        pending_replan_fields=["location"],
    )
    result = _handle_confirmation(state)

    assert result["turn_complete"] is True
    assert result["pending_replan_confirmation"] is True
    assert result["pending_replan_fields"] == ["location"]
