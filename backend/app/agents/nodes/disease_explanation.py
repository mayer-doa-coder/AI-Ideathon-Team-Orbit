"""disease_explanation — turns State.disease_result (populated by
disease_detection) into the farmer-facing response. Every factual sentence
names the source it came from — crop.health or GPT-5.6 Sol — the same
citation discipline `crop_recommendation` applies to the knowledge base and
`market_price_lookup` applies to the DAM snapshot.

Deliberately not an LLM call: the diagnosis, confidence, and treatment text
are already sitting in `disease_result` exactly as the source APIs returned
them, so formatting them here can't invent or soften anything — mirrors why
`market_price_lookup` builds its verdict text with a deterministic formatter
rather than an LLM. The one clarifying question asked when sources disagree
is GPT-5.6 Sol's own `clarifying_question` (produced during its
verification call in disease_detection, since it's the one that actually
looked at the photo), never guessed here.

Runs right after disease_detection regardless of whether identification
succeeded, so it's the single place a disease-photo turn ends the turn from.
"""
from langchain_core.messages import AIMessage

from app.agents.state import AgentState

FALLBACK_CLARIFYING_QUESTION = "Could you describe where on the plant the symptoms are worst?"


def _badge(confidence_level: str | None) -> dict | None:
    if confidence_level == "high":
        return {"label": "Cross-verified", "level": "high"}
    if confidence_level == "low":
        return {"label": "Tentative — sources disagree", "level": "low"}
    return None


def _no_crop_health_message() -> str:
    return (
        "I couldn't reach the disease-identification service (crop.health) just now, so I won't guess — "
        "please try again shortly, or describe the symptoms you're seeing in words."
    )


def _unconfirmed_message(crop_health: dict) -> str:
    return (
        f"crop.health identified **{crop_health['disease_name']}** as the most likely match "
        f"({crop_health['confidence']:.0%} confidence), but I couldn't get GPT-5.6 Sol's second opinion to "
        "confirm it, so I'm not calling it a diagnosis yet. Please try again, or describe the symptoms "
        "you're seeing."
    )


def _high_confidence_message(final_diagnosis: str, crop_health: dict, gpt: dict) -> str:
    lines = [
        f"**Diagnosis: {final_diagnosis}** — identified by crop.health "
        f"({crop_health['confidence']:.0%} confidence) and confirmed by GPT-5.6 Sol's visual read of the "
        f"same photo ({gpt['visual_evidence']})."
    ]
    if crop_health.get("treatment"):
        lines.append(f"\n**Treatment plan (crop.health):** {crop_health['treatment']}")
    return "\n".join(lines)


def _low_confidence_message(crop_health: dict, gpt: dict) -> str:
    lines = [
        f"crop.health's top read was **{crop_health['disease_name']}** "
        f"({crop_health['confidence']:.0%} confidence), but GPT-5.6 Sol, looking at the same photo, leans "
        f"toward **{gpt['disease_name']}** instead — it's going on {gpt['visual_evidence']}.",
        f"\nWhy they disagree: {gpt['reasoning']}",
        f"\nOne question before I give you a treatment plan: {gpt.get('clarifying_question') or FALLBACK_CLARIFYING_QUESTION}",
    ]
    return "\n".join(lines)


def disease_explanation(state: AgentState) -> dict:
    result = state.get("disease_result")
    if not result:
        return {}

    crop_health = result.get("crop_health")
    gpt = result.get("gpt_verification")
    confidence_level = result.get("confidence_level")
    final_diagnosis = result.get("final_diagnosis")

    if not crop_health:
        message_text = _no_crop_health_message()
    elif confidence_level == "high" and gpt and final_diagnosis:
        message_text = _high_confidence_message(final_diagnosis, crop_health, gpt)
    elif confidence_level == "low" and gpt:
        message_text = _low_confidence_message(crop_health, gpt)
    else:
        # crop.health succeeded but GPT-5.6 Sol's verification call itself
        # failed — no second opinion, so no confirmed diagnosis either.
        message_text = _unconfirmed_message(crop_health)

    badge = _badge(confidence_level)
    return {
        "turn_complete": True,
        "messages": [AIMessage(content=message_text, additional_kwargs={"badge": badge} if badge else {})],
    }
