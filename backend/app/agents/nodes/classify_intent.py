from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agents.state import REQUIRED_FARM_FIELDS, AgentState, Intent
from app.core.config import settings

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "classify_intent.md"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class ExtractedProfile(BaseModel):
    location: str | None = None
    acres: float | None = None
    soil_type: str | None = None
    water_availability: str | None = None
    budget: float | None = None
    season: str | None = None


class ScenarioParams(BaseModel):
    rainfall_change_pct: float | None = None
    budget_change_pct: float | None = None
    apply_to_plan: bool = False
    description: str | None = None


class MarketplaceQuery(BaseModel):
    product: str | None = None
    district: str | None = None
    quantity_kg: float | None = None


class MarketPriceQuery(BaseModel):
    crop: str | None = None
    district: str | None = None
    quantity_kg: float | None = None
    storage_available: bool | None = None
    urgent_cash_needed: bool | None = None
    storage_cost_bdt_per_unit_per_month: float | None = None


class IntentClassification(BaseModel):
    intent: Intent
    extracted_profile: ExtractedProfile = Field(default_factory=ExtractedProfile)
    selected_crop: str | None = None
    scenario_params: ScenarioParams | None = None
    marketplace_query: MarketplaceQuery | None = None
    market_price_query: MarketPriceQuery | None = None
    # Only meaningful (and only asked for in the prompt) when the context
    # says a replan confirmation is pending — True/False for a clear
    # yes/no, null if the reply doesn't actually answer that question.
    confirms_pending_replan: bool | None = None


_llm = ChatOpenAI(
    model=settings.chat_model, temperature=0, api_key=settings.openai_api_key
).with_structured_output(IntentClassification)


def _last_ai_question(messages: list, before_index: int | None) -> str | None:
    """The agent's most recent question, so a bare reply like "100" can be
    read in light of what was actually asked ("How many acres...") instead
    of being ambiguous on its own."""
    if before_index is None:
        return None
    for m in reversed(messages[:before_index]):
        if isinstance(m, AIMessage) and m.content:
            return m.content
    return None


def classify_intent(state: AgentState) -> dict:
    messages = state["messages"]
    last_human_idx = next(
        (i for i in range(len(messages) - 1, -1, -1) if isinstance(messages[i], HumanMessage)), None
    )
    latest_text = messages[last_human_idx].content if last_human_idx is not None else ""
    last_question = _last_ai_question(messages, last_human_idx)

    context_lines = [
        f"Current farm profile: {state.get('farm_profile') or {}}",
        f"Still missing: {state.get('missing_fields') or []}",
    ]
    if last_question:
        context_lines.append(f'The agent\'s immediately preceding question to the farmer was: "{last_question}"')
    if state.get("crop_candidates"):
        names = [c["name"] for c in state["crop_candidates"]]
        context_lines.append(f"Crop candidates currently shown to the farmer: {names}")
    if state.get("season_plan"):
        context_lines.append("A season plan already exists for this farmer.")
    if state.get("pending_replan_confirmation"):
        fields = ", ".join(state.get("pending_replan_fields") or [])
        context_lines.append(
            f"IMPORTANT: the farmer was just asked whether to build a completely new crop "
            f"recommendation and season plan, because their {fields} changed. Determine from "
            f"their latest message whether this is a clear yes, a clear no, or unclear, and set "
            f"confirms_pending_replan accordingly."
        )
    context_lines.append(f"Farmer's latest message: {latest_text}")

    result: IntentClassification = _llm.invoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(context_lines)},
        ]
    )

    merged_profile = dict(state.get("farm_profile") or {})
    # Only apply extracted fields when the farmer is actually stating/updating
    # their own farm's details (intent == "slot_fill"). A place name can
    # appear in an unrelated question ("what's the temperature in Bogura?",
    # classified as agro_question) — opportunistic extraction must not let
    # that silently overwrite the farm's real, committed profile and trigger
    # a false "your location changed, want a new plan?" flow downstream in
    # supervisor_router. Marketplace/market_price queries have their own
    # separate district fields and are untouched by this gate.
    if result.intent == "slot_fill":
        for field, value in result.extracted_profile.model_dump().items():
            if value is not None:
                merged_profile[field] = value
    missing = [f for f in REQUIRED_FARM_FIELDS if f not in merged_profile]

    update: dict = {
        "intent": result.intent,
        "farm_profile": merged_profile,
        "missing_fields": missing,
        "is_scenario": False,
    }

    if state.get("pending_replan_confirmation"):
        update["confirms_pending_replan"] = result.confirms_pending_replan

    if result.selected_crop:
        candidate_names = {c["name"].lower() for c in state.get("crop_candidates") or []}
        if result.selected_crop.lower() in candidate_names:
            update["selected_crop"] = result.selected_crop

    if result.intent == "scenario" and result.scenario_params:
        sp = result.scenario_params
        has_new_number = sp.rainfall_change_pct is not None or sp.budget_change_pct is not None
        if has_new_number:
            # A genuinely new "what if" — start fresh, don't blend with
            # whatever scenario was discussed earlier in the thread.
            merged = {
                "rainfall_change_pct": sp.rainfall_change_pct,
                "budget_change_pct": sp.budget_change_pct,
                "apply_to_plan": sp.apply_to_plan,
                "description": sp.description,
            }
        else:
            # A bare follow-up with no number of its own ("update the plan",
            # "to the best of your knowledge") — reuse the prior scenario's
            # numbers rather than losing them, only flipping apply_to_plan.
            merged = dict(state.get("scenario_override") or {})
            merged["apply_to_plan"] = sp.apply_to_plan
            if sp.description:
                merged["description"] = sp.description
        update["scenario_override"] = merged

    if result.intent == "marketplace" and result.marketplace_query:
        update["marketplace_query"] = result.marketplace_query.model_dump()

    if result.intent == "market_price" and result.market_price_query:
        query = result.market_price_query.model_dump()
        if not query.get("crop") and state.get("selected_crop"):
            query["crop"] = state["selected_crop"]
        update["market_price_query"] = query

    return update
