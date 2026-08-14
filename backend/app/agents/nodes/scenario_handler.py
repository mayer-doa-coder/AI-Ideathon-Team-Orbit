"""Confidence-checks the scenario parameter extracted by classify_intent.

Two distinct farmer intents land here, distinguished by `apply_to_plan`:
- A plain "what if" question (apply_to_plan=False) gets a narrated delta —
  the committed plan is never touched.
- "update the plan" / "apply that" / "to the best of your knowledge"
  (apply_to_plan=True) actually commits a change. Budget, area, and
  input-choice requests all go through `generate_season_plan` — the same
  grounded LLM call `season_planner` uses — with the farmer's request
  passed as a revision instruction. The model decides which levers
  actually make agronomic sense (reduce fertilizer, drop a non-essential
  input, shrink the area, substitute a cheaper grounded alternative)
  instead of this node hardcoding one fixed strategy for one fixed
  scenario type. Whatever it proposes is then priced by the same
  deterministic `calculate_financials` — nothing about cost is ever
  trusted directly from the LLM, only what the real function computes
  from the plan it produced.
  Rainfall-only asks to "apply" never auto-commit — we only have one real
  forecast per location, not a simulator, so fabricating an alternate one
  to regenerate against would violate the "never invent a number" rule;
  real forecast-driven adjustments are the monitor graph's job.
If there's nothing at all to act on (a bare "update the plan" with
nothing established earlier in the thread), this asks a real clarifying
question instead of guessing or echoing back an internal label.
"""
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.nodes.season_planner import generate_season_plan, retrieve_grounded_docs
from app.agents.state import AgentState
from app.db.models import Farm, Plan
from app.db.session import SessionLocal
from app.tools.financials import apply_budget_constraint
from app.tools.financials import calculate_financials as compute_financials


def _commit_plan_update(
    farmer_id: str,
    season_plan: dict,
    financials: dict,
    new_acres: float | None,
    new_budget: float | None,
) -> dict | None:
    """Writes the revised plan back to Postgres and, when the scenario
    implied a real change to the farm itself (a new area, a new budget —
    not just a hypothetical plan tweak), updates `Farm` too. Returns the
    farm's fresh profile dict so the caller can push it into the *same*
    turn's response instead of making the farmer wait for their next
    message before the dashboard catches up (`load_memory` would
    eventually reload it, but not until then).
    """
    db = SessionLocal()
    try:
        farm = db.query(Farm).filter(Farm.user_id == int(farmer_id)).first()
        if not farm:
            return None
        plan = db.query(Plan).filter(Plan.farm_id == farm.id).first()
        if not plan:
            return None
        plan.season_plan = season_plan
        plan.financials = financials
        if new_acres:
            farm.acres = new_acres
        if new_budget:
            farm.budget = new_budget
        db.commit()
        return {
            "location": farm.location,
            "lat": farm.lat,
            "lon": farm.lon,
            "acres": farm.acres,
            "soil_type": farm.soil_type,
            "water_availability": farm.water_availability,
            "budget": farm.budget,
            "season": farm.season,
        }
    finally:
        db.close()


def _build_instruction(state: AgentState, override: dict, budget_pct, rainfall_pct) -> str:
    parts = []
    if budget_pct is not None:
        parts.append(f"Target budget is {budget_pct:+.0f}% relative to the original.")
    if rainfall_pct is not None:
        parts.append(f"Rainfall assumption: {rainfall_pct:+.0f}% relative to the current forecast.")
    if override.get("description"):
        parts.append(f"What the farmer is asking for: {override['description']}")
    last_human = next(
        (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None
    )
    if last_human:
        parts.append(f'Farmer\'s latest message, verbatim: "{last_human}"')
    return " ".join(parts)


def scenario_handler(state: AgentState) -> dict:
    override = state.get("scenario_override") or {}
    season_plan = state.get("season_plan") or {}
    crop = state.get("selected_crop") or ""
    profile = state.get("farm_profile") or {}
    acres = profile.get("acres") or 1.0
    weather = state.get("weather_data")
    baseline = state.get("financials") or compute_financials(season_plan, crop, acres)

    budget_pct = override.get("budget_change_pct")
    rainfall_pct = override.get("rainfall_change_pct")
    apply_to_plan = bool(override.get("apply_to_plan"))
    has_instruction = (
        budget_pct is not None or rainfall_pct is not None or bool(override.get("description"))
    )

    if not has_instruction:
        text = (
            (
                "Update it based on what, exactly — a budget change, a smaller area, a different "
                "input, or something else? Tell me the specifics and I'll apply it."
            )
            if apply_to_plan
            else (
                "I couldn't identify a specific scenario to simulate — try something like "
                '"what if rainfall drops 30%?" or "what if my budget is cut 40%?"'
            )
        )
        return {
            "trace_log": [],
            "turn_complete": True,
            "is_scenario": True,
            "messages": [AIMessage(content=text)],
        }

    # Rainfall-only asks to "apply" can't be committed — we only have one
    # real forecast, not a simulator; fabricating an alternate one to
    # regenerate the plan against would break the "never invent data" rule.
    rainfall_only_apply = (
        apply_to_plan
        and rainfall_pct is not None
        and budget_pct is None
        and not override.get("description")
    )
    if rainfall_only_apply:
        return {
            "trace_log": [],
            "turn_complete": True,
            "is_scenario": True,
            "messages": [
                AIMessage(
                    content=(
                        "I can't commit a rainfall-driven plan change from a hypothetical — I only "
                        "have the one real forecast for your location, not a simulator. If actual "
                        "rainfall shifts this much, the monitor agent watches the real forecast and "
                        "will adjust your plan automatically."
                    )
                )
            ],
        }

    if not apply_to_plan:
        return _narrate_only(override, season_plan, profile, baseline, budget_pct, rainfall_pct)

    return _apply_to_plan(state, override, season_plan, profile, crop, acres, weather, baseline, budget_pct)


def _narrate_only(override, season_plan, profile, baseline, budget_pct, rainfall_pct) -> dict:
    lines: list[str] = []
    trace: list[dict] = []

    if budget_pct is not None:
        original_budget = profile.get("budget") or baseline["cost"]
        new_budget = original_budget * (1 + budget_pct / 100)
        shortfall = baseline["cost"] - new_budget
        trace.append(
            {
                "type": "financial",
                "tool": "calculate_financials",
                "paramsDisplay": f"scenario budget_change_pct={budget_pct}",
                "params": {"original_budget": original_budget, "new_budget": round(new_budget)},
                "response": {"required_cost": baseline["cost"], "shortfall": round(shortfall)},
                "summary": f"required cost ৳{baseline['cost']:,} vs new budget ৳{new_budget:,.0f}",
            }
        )
        if shortfall > 0:
            lines.append(
                f"With your budget cut {abs(budget_pct):.0f}%, you'd have ৳{new_budget:,.0f} "
                f"available but the plan needs ৳{baseline['cost']:,} — a shortfall of "
                f"৳{shortfall:,.0f}. Say \"update the plan\" if you'd like me to apply this."
            )
        else:
            lines.append(
                f"Even with a {abs(budget_pct):.0f}% budget cut you'd still have ৳{new_budget:,.0f} "
                f"available against a required cost of ৳{baseline['cost']:,}, so the plan still fits."
            )

    if rainfall_pct is not None:
        direction = "less" if rainfall_pct < 0 else "more"
        advice = (
            "plan for supplemental irrigation between the scheduled dates"
            if rainfall_pct < 0
            else "watch for waterlogging and delay fertilizer top-dressing around wet days"
        )
        lines.append(
            f"With {abs(rainfall_pct):.0f}% {direction} rainfall than forecast, your irrigation "
            f"schedule would need adjusting — {advice}. This doesn't change your committed plan; "
            f"ask me to redo the season plan under this assumption if you want it updated."
        )

    if not lines:
        description = override.get("description")
        lines.append(
            f"Here's what I understood: {description}. Could you give me a specific number to "
            f"simulate?"
            if description
            else "Could you give me a specific number to simulate — a budget or rainfall percentage?"
        )

    return {
        "trace_log": trace,
        "turn_complete": True,
        "is_scenario": True,
        "messages": [AIMessage(content="\n\n".join(lines))],
    }


def _apply_to_plan(state, override, season_plan, profile, crop, acres, weather, baseline, budget_pct) -> dict:
    instruction = _build_instruction(state, override, budget_pct, override.get("rainfall_change_pct"))
    docs, trace = retrieve_grounded_docs(crop)

    # Computed once, used both for the deterministic fallback and for the
    # honesty check / Farm.budget update below — this IS the farmer's new
    # stated budget, a fact about them, independent of whether the plan we
    # produce actually fits it.
    target_budget = None
    if budget_pct is not None:
        original_budget = profile.get("budget") or baseline["cost"]
        target_budget = original_budget * (1 + budget_pct / 100)

    try:
        new_plan, new_acres = generate_season_plan(
            profile, crop, weather, docs, acres, extra_instruction=instruction
        )
        new_financials = compute_financials(new_plan, crop, new_acres)
    except Exception:
        # LLM regeneration failed — fall back to the deterministic
        # fertilizer scaler for a budget ask; otherwise there's nothing
        # safe to do but report the failure honestly.
        if target_budget is not None:
            new_plan = apply_budget_constraint(season_plan, crop, acres, target_budget)
            new_financials = compute_financials(new_plan, crop, acres)
            new_acres = acres
        else:
            return {
                "trace_log": trace,
                "turn_complete": True,
                "is_scenario": True,
                "messages": [
                    AIMessage(
                        content="Something went wrong trying to apply that change — could you try rephrasing the request?"
                    )
                ],
            }

    acres_changed = new_acres != acres
    trace.append(
        {
            "type": "financial",
            "tool": "generate_season_plan",
            "paramsDisplay": f'instruction="{instruction[:80]}"' + ("..." if len(instruction) > 80 else ""),
            "params": {"instruction": instruction, "acres": new_acres},
            "response": {
                "old_cost": baseline["cost"],
                "new_cost": new_financials["cost"],
                "old_profit": baseline["profit"],
                "new_profit": new_financials["profit"],
                "acres_changed": acres_changed,
            },
            "summary": f"plan revised — cost ৳{baseline['cost']:,} to ৳{new_financials['cost']:,}",
        }
    )

    lines = [new_plan.get("reasoning") or "Updated your plan for this."]
    lines.append(
        f"Cost: ৳{baseline['cost']:,} to ৳{new_financials['cost']:,}. "
        f"Profit: ৳{baseline['profit']:,} to ৳{new_financials['profit']:,}."
        + (f" Acreage: {acres} to {new_acres}." if acres_changed else "")
    )

    if target_budget is not None:
        gap = new_financials["cost"] - target_budget
        tolerance = max(25, round(target_budget * 0.005))
        if gap > tolerance:
            lines.append(
                f"Still ৳{gap:,.0f} over your ৳{target_budget:,.0f} target even after this — I've "
                f"kept the revised plan since it's the closest realistic fit, but you may need to "
                f"raise the budget further or shrink the area more."
            )

    new_farm_profile = _commit_plan_update(
        state["farmer_id"],
        new_plan,
        new_financials,
        new_acres if acres_changed else None,
        target_budget,
    )

    update: dict = {
        "trace_log": trace,
        "turn_complete": True,
        "is_scenario": True,
        "season_plan": new_plan,
        "financials": new_financials,
        # Lets the sources panel show what actually grounded *this* plan —
        # without this, it keeps showing whatever the original plan cited.
        "retrieved_docs": docs,
        "messages": [AIMessage(content="\n".join(lines))],
    }
    if new_farm_profile:
        # Pushes the corrected acres/budget into this same turn's response
        # instead of leaving the dashboard stale until the farmer's next
        # message triggers load_memory's reload.
        update["farm_profile"] = new_farm_profile
    return update
