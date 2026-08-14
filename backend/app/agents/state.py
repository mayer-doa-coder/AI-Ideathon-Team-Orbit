"""Shared state schemas for the LangGraph graphs.

`FarmProfile` is the shape both graphs read/write the farm's fixed
attributes as; `SeasonPlan` is the shape both graphs read/write the
season plan as (see its own docstring — this is the one contract that
makes the monitor graph able to act on a plan the conversation graph
produced); `AgentState` is the conversation graph's full state (see
`graph_conversation.py`) and `MonitorState` is the monitor graph's full
state (see `graph_monitor.py`). All are plain `TypedDict`s — LangGraph
merges each node's returned partial dict into the running state, using the
field-level reducers annotated below (`messages`, `trace_log`) where a node
needs to append instead of overwrite.
"""
import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.tools.weather import ForecastResult

REQUIRED_FARM_FIELDS = ["location", "acres", "soil_type", "water_availability", "budget", "season"]

# Fields that, if changed once a plan already exists, invalidate crop
# suitability itself (a different location/soil/water/season means
# different crops fit) — a change to any of these routes through
# `core_change_handler`'s "I've updated this, want a whole new plan?"
# flow. Deliberately excludes acres/budget: those are scale/cost factors
# that `scenario_handler` already regenerates the *same* crop's plan for,
# without needing to re-pick a crop entirely.
CORE_REPLAN_FIELDS = ["location", "soil_type", "water_availability", "season"]

Intent = Literal["slot_fill", "scenario", "agro_question", "off_topic", "chitchat", "marketplace", "market_price"]


class FarmProfile(TypedDict, total=False):
    location: str
    lat: float
    lon: float
    acres: float
    soil_type: str
    water_availability: str
    budget: float
    season: str


class DiseaseCandidate(TypedDict):
    disease_name: str
    confidence: float
    treatment: str


class CropHealthResult(TypedDict):
    disease_name: str
    confidence: float
    treatment: str
    top_candidates: list[DiseaseCandidate]


class GPTDiseaseVerification(TypedDict):
    agrees: bool
    disease_name: str
    visual_evidence: str
    reasoning: str
    # Only set when agrees is False — the one question disease_explanation
    # asks the farmer before offering a treatment plan, e.g. "are the spots
    # mostly on the older bottom leaves or the new growth at the top?".
    # Produced by GPT-5.6 Sol during the same vision call, not invented by
    # the (deliberately non-LLM) explanation node — see nodes/disease_explanation.py.
    clarifying_question: str | None


class DiseaseResult(TypedDict):
    image_provided: bool
    crop_health: CropHealthResult | None
    gpt_verification: GPTDiseaseVerification | None
    final_diagnosis: str | None
    # "high" only when crop.health's top candidate and GPT-5.6 Sol's pick
    # agree; "low" on any disagreement; None when no diagnosis could be
    # made at all (see nodes/disease_detection.py).
    confidence_level: Literal["high", "low"] | None


class VoiceInput(TypedDict):
    used: bool
    transcribed_text: str | None
    stt_error: str | None


class VoiceOutput(TypedDict):
    requested: bool
    audio_path: str | None
    tts_error: str | None


class CropCandidate(TypedDict):
    id: str
    name: str
    suitability: str
    water_need: str
    risk_level: str
    profit_estimate: float
    reasoning_knowledge: str
    reasoning_weather: str
    # Real DAM-sourced market snapshot + SELL NOW/STORE/WAIT verdict for this
    # crop, or None if unmapped/not yet ingested — see
    # nodes/crop_recommendation._attach_market_intelligence.
    market: dict | None


class FertilizerScheduleItem(TypedDict):
    name: str
    stage: str
    date: str  # ISO YYYY-MM-DD
    amount_kg_per_acre: float
    status: str  # "pending" | "applied"
    adjusted: bool
    adjustment_note: str | None
    # The item's `date` before the most recent monitor adjustment, or None if
    # never adjusted — lets the frontend timeline show "moved from X to Y".
    date_before_adjustment: str | None


class IrrigationScheduleItem(TypedDict):
    date: str
    note: str
    status: str


class WeedCheckpoint(TypedDict):
    date: str
    note: str


class PestRiskItem(TypedDict):
    name: str
    risk_window_start: str
    risk_window_end: str
    status: str  # "watching" | "active"
    adjusted: bool
    adjustment_note: str | None
    prevention: str


class SeasonPlan(TypedDict):
    """Produced by the conversation graph's `season_planner` node (grounded
    in RAG + weather, LLM-authored day-offsets converted to absolute ISO
    dates in Python), persisted to `plans.season_plan`, and read back
    unmodified by the monitor graph (see `graph_monitor.load_initial_state`)
    — this is the one shape both graphs agree on. `compare_thresholds` reads
    `fertilizer_schedule[].status`/`.date` and `pest_risks[].risk_window_*`
    directly, so those fields must always be concrete dates, never free text.
    """

    crop: str
    sowing_window: dict  # {"start": ISO date, "end": ISO date}
    fertilizer_schedule: list[FertilizerScheduleItem]
    irrigation_schedule: list[IrrigationScheduleItem]
    pest_risks: list[PestRiskItem]
    weed_checkpoints: list[WeedCheckpoint]
    harvest_window: dict  # {"start": ISO date, "end": ISO date}
    seed_rate_kg_per_acre: float
    expected_yield_ton_per_acre: float
    reasoning: str


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    farmer_id: str
    intent: Intent | None
    farm_profile: FarmProfile
    # A snapshot of `farm_profile` exactly as it is in Postgres as of the
    # start of this turn — refreshed unconditionally by `load_memory` every
    # turn, *before* `classify_intent` may have merged in a new value from
    # the farmer's latest message. This is what `core_change_handler` diffs
    # `farm_profile` against to detect "did a core fact actually change this
    # turn", since by the time the router runs, `farm_profile` itself
    # already holds the new (not-yet-committed) value.
    committed_farm_profile: FarmProfile
    missing_fields: list[str]
    weather_data: dict[str, Any] | None
    retrieved_docs: list[dict]
    crop_candidates: list[CropCandidate]
    selected_crop: str | None
    season_plan: SeasonPlan | None
    financials: dict[str, Any] | None
    scenario_override: dict[str, Any] | None
    is_scenario: bool
    marketplace_query: dict[str, Any] | None
    market_price_query: dict[str, Any] | None
    # Browser-reported current position for *this* message, not the farm's
    # registered location — see ChatRequest.lat/lon. Reset every turn by
    # `chat.py` rather than carried in `farm_profile`, since where the
    # farmer is chatting from and where their farm is aren't the same thing.
    current_location: dict[str, float] | None
    # Base64-encoded photo attached to *this* message, not carried over
    # between turns — same reset-every-turn treatment as current_location,
    # set fresh by chat.py from the request payload. Its presence (not
    # `intent`) is what routes a turn to disease_detection; see
    # router.intake_router.
    uploaded_image: str | None
    disease_result: DiseaseResult | None
    # Base64-encoded voice message attached to *this* message — same
    # reset-every-turn treatment as uploaded_image, set fresh by chat.py from
    # the request payload. Its presence (not `intent`) is what routes a turn
    # to voice_input; see router.intake_router.
    uploaded_audio: str | None
    voice_input: VoiceInput
    voice_output: VoiceOutput
    # True right after `core_change_handler` has asked "want a whole new
    # plan for this?" — the *next* turn, this takes routing priority over
    # normal intent classification, so a bare "yes"/"no" (which classify_intent
    # might otherwise misread as chitchat) still reaches the handler.
    pending_replan_confirmation: bool
    # Which CORE_REPLAN_FIELDS triggered the pending question — used to
    # phrase the follow-up message and to know what changed.
    pending_replan_fields: list[str]
    # Set by classify_intent only when pending_replan_confirmation was true
    # on entry — True/False if the farmer's reply was a clear yes/no, None
    # if it couldn't tell.
    confirms_pending_replan: bool | None
    # True from the moment a "yes" clears crop_candidates/season_plan for a
    # fresh replan until `persist` commits the new one. While true,
    # `load_memory` must NOT resync crop_candidates/selected_crop/
    # season_plan/financials from Postgres — the committed row still holds
    # the *previous* plan (nothing new has been persisted yet), so its
    # normal "the monitor may have changed this out-of-band, always trust
    # Postgres" resync would silently overwrite the freshly (re)computed,
    # not-yet-committed candidates with stale data on the very next turn.
    replanning: bool
    turn_complete: bool
    # Additive: every node appends its own new entries rather than replacing
    # the list, so the trace stays cumulative for the whole thread.
    trace_log: Annotated[list[dict], operator.add]


def new_state(farmer_id: str) -> AgentState:
    return AgentState(
        messages=[],
        farmer_id=farmer_id,
        intent=None,
        farm_profile={},
        committed_farm_profile={},
        missing_fields=list(REQUIRED_FARM_FIELDS),
        weather_data=None,
        retrieved_docs=[],
        crop_candidates=[],
        selected_crop=None,
        season_plan=None,
        financials=None,
        scenario_override=None,
        is_scenario=False,
        marketplace_query=None,
        market_price_query=None,
        current_location=None,
        uploaded_image=None,
        disease_result=None,
        uploaded_audio=None,
        voice_input={"used": False, "transcribed_text": None, "stt_error": None},
        voice_output={"requested": False, "audio_path": None, "tts_error": None},
        pending_replan_confirmation=False,
        pending_replan_fields=[],
        confirms_pending_replan=None,
        replanning=False,
        turn_complete=False,
        trace_log=[],
    )


class MonitorState(TypedDict):
    farm_id: int
    farm: FarmProfile
    # Loaded from Postgres before the graph runs, not recomputed by a node —
    # the monitor's "memory" of a farm is the `plans` table, not graph state.
    season_plan: SeasonPlan
    financials: dict

    weather_data: ForecastResult | None
    # Present only on the simulate-trigger demo path; when set, fetch_weather
    # uses this instead of calling Open-Meteo.
    weather_override: ForecastResult | None

    triggered: bool
    trigger_reason: str | None
    # Structured detail behind `trigger_reason` (which schedule item, which
    # date, how much rain) — `recompute_season_plan` needs this to know
    # exactly what to adjust; `trigger_reason` alone is just the display string.
    trigger_context: dict | None
    updated_plan: SeasonPlan | None
    updated_financials: dict | None
