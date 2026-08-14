"""disease_detection — Kindwise crop.health identification plus a GPT-5.6
Sol vision cross-check, run instead of the normal slot-fill/intent intake
path whenever the farmer's message carries an uploaded image (see
`router.intake_router`).

Two real external calls, both traced like `weather_tool` traces Open-Meteo:
crop.health's top-3 candidate diseases, then GPT-5.6 Sol looking at the same
photo plus those candidates as context, stating whether it agrees and what
specific visual evidence it's using. `confidence_level` is only "high" when
the two agree.

This node only gathers data into `disease_result` — it never writes the
farmer-facing message or ends the turn. That's `disease_explanation`'s job
(deliberately split out so the citation/wording logic has nothing to do
with the API calls). Never invents a diagnosis: if crop.health fails, or if
GPT-5.6 Sol's verification call fails, `final_diagnosis` stays None rather
than falling back to a model guess presented as confirmed.
"""
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.agents.state import AgentState
from app.core.config import settings
from app.tools.crop_health import CropHealthAPIError, identify_disease, top_candidates

VISION_MODEL = "gpt-5.6-sol"


class GPTDiseaseVerification(BaseModel):
    agrees: bool = Field(description="Whether GPT-5.6 Sol agrees with crop.health's top candidate")
    disease_name: str = Field(description="GPT-5.6 Sol's own pick — the top candidate's name if it agrees")
    visual_evidence: str = Field(description='Specific visual detail, e.g. "yellow halos on older leaves"')
    reasoning: str
    clarifying_question: str | None = Field(
        default=None,
        description=(
            "Only when agrees=False: ONE question whose answer would help a farmer distinguish between "
            'the two candidate diseases, e.g. "are the spots mostly on the older bottom leaves or the new '
            'growth at the top?". Leave null when agrees=True.'
        ),
    )


_vision_llm = ChatOpenAI(
    model=VISION_MODEL, temperature=0, api_key=settings.openai_api_key
).with_structured_output(GPTDiseaseVerification)


def _verify_with_gpt(image_base64: str, candidates: list[dict]) -> GPTDiseaseVerification:
    candidates_text = "\n".join(
        f"{i + 1}. {c['disease_name']} (confidence {c['confidence']:.2f}): {c['treatment'] or 'no treatment info'}"
        for i, c in enumerate(candidates)
    )
    prompt_text = (
        "A crop.health image classifier produced these top-3 candidate diagnoses for this crop photo:\n"
        f"{candidates_text}\n\n"
        "Look at the photo yourself. State whether you agree with candidate #1, or which of the other "
        "candidates you think is more likely instead. Name the specific visual evidence you're using "
        '(e.g. "yellow halos on older leaves"), not a generic description. If you disagree, also propose '
        "ONE clarifying question a farmer could answer to help tell the two candidates apart — leave it "
        "null if you agree."
    )
    request = {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        ],
    }
    return _vision_llm.invoke([request])


def disease_detection(state: AgentState) -> dict:
    image_base64 = state.get("uploaded_image")
    if not image_base64:
        return {}

    trace: list[dict] = []
    crop_health_params = {"details": ["treatment", "description"], "top_k": 3}

    try:
        raw_response = identify_disease(image_base64, details=crop_health_params["details"])
    except CropHealthAPIError as exc:
        trace.append(
            {
                "type": "disease_detection",
                "tool": "crop_health_identify",
                "paramsDisplay": "image=<uploaded photo>",
                "params": crop_health_params,
                "response": {"error": str(exc)},
                "summary": "crop.health identification failed — no diagnosis given",
            }
        )
        return {
            "trace_log": trace,
            "disease_result": {
                "image_provided": True,
                "crop_health": None,
                "gpt_verification": None,
                "final_diagnosis": None,
                "confidence_level": None,
            },
        }

    candidates = top_candidates(raw_response, limit=3)
    top = candidates[0] if candidates else None

    trace.append(
        {
            "type": "disease_detection",
            "tool": "crop_health_identify",
            "paramsDisplay": "image=<uploaded photo>",
            "params": crop_health_params,
            "response": raw_response,
            "summary": (
                f"top candidate: {top['disease_name']} ({top['confidence']:.0%} confidence)"
                if top
                else "no disease candidates returned"
            ),
        }
    )

    crop_health_result = (
        {
            "disease_name": top["disease_name"],
            "confidence": top["confidence"],
            "treatment": top["treatment"],
            "top_candidates": candidates,
        }
        if top
        else None
    )

    gpt_verification = None
    final_diagnosis = None
    confidence_level = None

    if top:
        try:
            gpt_result = _verify_with_gpt(image_base64, candidates)
        except Exception as exc:  # noqa: BLE001 — GPT verification failing must not fabricate a diagnosis
            trace.append(
                {
                    "type": "disease_detection",
                    "tool": "gpt_vision_verify",
                    "paramsDisplay": f"model={VISION_MODEL}, image=<uploaded photo>",
                    "params": {"model": VISION_MODEL, "candidates": candidates},
                    "response": {"error": str(exc)},
                    "summary": "GPT-5.6 Sol verification failed — no confirmed diagnosis",
                }
            )
        else:
            gpt_verification = gpt_result.model_dump()
            agrees_with_top = gpt_result.disease_name.strip().lower() == top["disease_name"].strip().lower()
            confidence_level = "high" if agrees_with_top else "low"
            final_diagnosis = top["disease_name"] if agrees_with_top else gpt_result.disease_name

            trace.append(
                {
                    "type": "disease_detection",
                    "tool": "gpt_vision_verify",
                    "paramsDisplay": f"model={VISION_MODEL}, image=<uploaded photo>",
                    "params": {"model": VISION_MODEL, "candidates": candidates},
                    "response": gpt_verification,
                    "summary": (
                        f"GPT-5.6 Sol {'agrees' if gpt_result.agrees else 'disagrees'}: {gpt_result.disease_name}"
                    ),
                    "badge": (
                        {"label": "Cross-verified", "level": "high"}
                        if confidence_level == "high"
                        else {"label": "Tentative — sources disagree", "level": "low"}
                    ),
                }
            )

    return {
        "trace_log": trace,
        "disease_result": {
            "image_provided": True,
            "crop_health": crop_health_result,
            "gpt_verification": gpt_verification,
            "final_diagnosis": final_diagnosis,
            "confidence_level": confidence_level,
        },
    }
