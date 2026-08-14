from datetime import date, timedelta
from pathlib import Path

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.state import AgentState
from app.core.config import settings
from app.db.session import SessionLocal
from app.tools.rag import is_grounded_enough, retrieve_agri_knowledge
from app.tools.web_search import web_search_as_docs

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "season_planner.md"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")


class FertilizerItem(BaseModel):
    name: str
    stage: str
    days_after_sowing: int
    amount_kg_per_acre: float


class IrrigationItem(BaseModel):
    days_after_sowing: int
    note: str


class PestRisk(BaseModel):
    name: str
    risk_window_start_days_after_sowing: int
    risk_window_end_days_after_sowing: int
    prevention: str


class WeedCheckpointItem(BaseModel):
    days_after_sowing: int
    note: str


class SeasonPlanOut(BaseModel):
    # Anchored to "today" (sowing hasn't happened yet — this plan is being
    # made now) so `compare_thresholds` can compare real forecast dates
    # against real schedule dates, not free text.
    sowing_start_days_from_today: int
    sowing_end_days_from_today: int
    # Anchored to sowing start, matching the "DAT" (days after transplanting/
    # sowing) convention the retrieved agronomic material already uses.
    harvest_start_days_after_sowing: int
    harvest_end_days_after_sowing: int
    fertilizer_schedule: list[FertilizerItem]
    irrigation_schedule: list[IrrigationItem]
    pest_risks: list[PestRisk]
    weed_checkpoints: list[WeedCheckpointItem]
    seed_rate_kg_per_acre: float
    expected_yield_ton_per_acre: float
    # Only set when an adjustment instruction explicitly implies planting a
    # different area than before (e.g. "I'll plant a smaller area") — null
    # on a normal first-time plan, where there's nothing to revise from.
    revised_acres: float | None = None
    reasoning: str


_llm = ChatOpenAI(
    model=settings.chat_model, temperature=0.2, api_key=settings.openai_api_key
).with_structured_output(SeasonPlanOut)


def retrieve_grounded_docs(crop: str) -> tuple[list[dict], list[dict]]:
    """Runs the standard fertilizer/irrigation/pest retrieval for `crop`,
    falling back to a web search per-topic when the knowledge base has
    nothing relevant. Returns (all_docs, trace_entries) — shared by the
    initial plan generation and by scenario-driven regeneration, so both
    ground themselves the same way instead of one reusing possibly-stale
    docs from an earlier turn.
    """
    queries = {
        "fertilizer": f"fertilizer application rate for {crop}",
        "irrigation": f"irrigation schedule for {crop}",
        "pest": f"major pests and diseases control measures for {crop}",
    }

    trace = []
    all_docs = []
    db = SessionLocal()
    try:
        for label, query in queries.items():
            docs = retrieve_agri_knowledge(db, query, crop=crop, k=4)
            trace.append(
                {
                    "type": "knowledge",
                    "tool": "retrieve_agri_knowledge",
                    "paramsDisplay": f'query="{query}", crop="{crop}"',
                    "params": {"query": query, "crop": crop, "top_k": 4},
                    "response": {
                        "chunks_retrieved": len(docs),
                        "sources": sorted({d["source_title"] for d in docs}),
                    },
                    "summary": f"{len(docs)} {label} chunks retrieved for {crop}",
                }
            )

            if not is_grounded_enough(docs):
                # Nothing relevant in the knowledge base for this
                # crop/topic — fall back to a real web search rather than
                # let the LLM reason from unrooted general knowledge for
                # this section.
                docs = web_search_as_docs(query, max_results=4)
                trace.append(
                    {
                        "type": "knowledge",
                        "tool": "web_search",
                        "paramsDisplay": f'query="{query}"',
                        "params": {"query": query},
                        "response": {
                            "chunks_retrieved": len(docs),
                            "urls": [d["url"] for d in docs if d.get("url")],
                        },
                        "summary": (
                            f"knowledge base had nothing for {label} — "
                            f"{len(docs)} web results used instead"
                        ),
                    }
                )

            all_docs.extend(docs)
    finally:
        db.close()

    return all_docs, trace


def generate_season_plan(
    profile: dict,
    crop: str,
    weather: dict | None,
    docs: list[dict],
    acres: float,
    extra_instruction: str = "",
) -> tuple[dict, float]:
    """Calls the LLM to produce a season plan grounded in `docs`, converts
    its day-offset output into absolute ISO dates, and returns
    `(season_plan_dict, effective_acres)`.

    `extra_instruction`, when given, is how `scenario_handler` asks for a
    plan revised under some constraint ("cut the budget 40%", "plant a
    smaller area", "switch to a cheaper fertilizer") — the LLM decides
    which levers make agronomic sense to pull, grounded in the same
    retrieved material, rather than the caller hardcoding one fixed
    strategy (e.g. always scaling fertilizer). `effective_acres` reflects
    `revised_acres` if the model set one, otherwise the `acres` passed in.
    """
    today = date.today()
    context_lines = [
        f"Selected crop: {crop}",
        f"Farm profile: {profile}",
        f"Today's date: {today.isoformat()}",
    ]
    if weather:
        heavy_rain_days = [
            d for d, mm in zip(weather["dates"], weather["daily_rainfall_mm"]) if mm >= 20
        ]
        context_lines.append(
            f"14-day forecast: rainfall by day {weather['daily_rainfall_mm']}, "
            f"heavy rain (>=20mm) on: {heavy_rain_days or 'none'}"
        )
    else:
        context_lines.append("No weather forecast available.")

    if extra_instruction:
        context_lines.append(f"IMPORTANT — revise the plan for this: {extra_instruction}")

    context_lines.append("Retrieved reference material:")
    for i, d in enumerate(docs, 1):
        context_lines.append(f"[{i}] {d['content']}")

    result: SeasonPlanOut = _llm.invoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(context_lines)},
        ]
    )

    sowing_start = today + timedelta(days=result.sowing_start_days_from_today)
    sowing_end = today + timedelta(days=result.sowing_end_days_from_today)
    harvest_start = sowing_start + timedelta(days=result.harvest_start_days_after_sowing)
    harvest_end = sowing_start + timedelta(days=result.harvest_end_days_after_sowing)

    def _date(days_after_sowing: int) -> str:
        return (sowing_start + timedelta(days=days_after_sowing)).isoformat()

    season_plan = {
        "crop": crop,
        "sowing_window": {"start": sowing_start.isoformat(), "end": sowing_end.isoformat()},
        "fertilizer_schedule": [
            {
                "name": item.name,
                "stage": item.stage,
                "date": _date(item.days_after_sowing),
                "amount_kg_per_acre": item.amount_kg_per_acre,
                "status": "pending",
                "adjusted": False,
                "adjustment_note": None,
                "date_before_adjustment": None,
            }
            for item in result.fertilizer_schedule
        ],
        "irrigation_schedule": [
            {"date": _date(item.days_after_sowing), "note": item.note, "status": "pending"}
            for item in result.irrigation_schedule
        ],
        "pest_risks": [
            {
                "name": item.name,
                "risk_window_start": _date(item.risk_window_start_days_after_sowing),
                "risk_window_end": _date(item.risk_window_end_days_after_sowing),
                "status": "watching",
                "adjusted": False,
                "adjustment_note": None,
                "prevention": item.prevention,
            }
            for item in result.pest_risks
        ],
        "weed_checkpoints": [
            {"date": _date(item.days_after_sowing), "note": item.note}
            for item in result.weed_checkpoints
        ],
        "harvest_window": {"start": harvest_start.isoformat(), "end": harvest_end.isoformat()},
        "seed_rate_kg_per_acre": result.seed_rate_kg_per_acre,
        "expected_yield_ton_per_acre": result.expected_yield_ton_per_acre,
        "reasoning": result.reasoning,
    }

    effective_acres = result.revised_acres if result.revised_acres else acres
    return season_plan, effective_acres


def season_planner(state: AgentState) -> dict:
    profile = state.get("farm_profile") or {}
    crop = state.get("selected_crop") or ""
    weather = state.get("weather_data")
    acres = profile.get("acres") or 1.0

    all_docs, trace = retrieve_grounded_docs(crop)
    season_plan, _ = generate_season_plan(profile, crop, weather, all_docs, acres)

    return {
        "season_plan": season_plan,
        "retrieved_docs": all_docs,
        "trace_log": trace,
    }
