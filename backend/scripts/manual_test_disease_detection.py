"""Manual, offline test for the disease_detection -> disease_explanation
pipeline. Mocks both external calls (crop.health's `identify_disease` and
GPT-5.6 Sol's vision `.invoke`) so it costs zero crop.health credits and
zero OpenAI tokens — crop.health only gives 100 free identification
credits total, so this is deliberately not a real API call.

Simulates the two response shapes the pipeline can produce:
  1. Both sources agree -> "high" confidence, treatment plan given directly.
  2. Sources disagree -> "low" confidence, both candidates shown, one
     clarifying question asked, no treatment plan yet.

Run with the backend venv active: `python scripts/manual_test_disease_detection.py`
"""
import json
from unittest.mock import patch

from app.agents.nodes.disease_detection import GPTDiseaseVerification, disease_detection
from app.agents.nodes.disease_explanation import disease_explanation
from app.agents.state import new_state

# A minimal but realistic crop.health raw response — same shape the real API
# returns under `result.disease.suggestions[]` (verified against the
# `kindwise-api-client` SDK's own dataclasses, not guessed).
CROP_HEALTH_RAW_RESPONSE = {
    "access_token": "fake-token-for-manual-test",
    "model_version": "2.1",
    "custom_id": None,
    "status": "COMPLETED",
    "result": {
        "is_plant": {"probability": 0.98, "binary": True},
        "crop": {"suggestions": [{"id": "c1", "name": "tomato", "probability": 0.95, "details": {}}]},
        "disease": {
            "suggestions": [
                {
                    "id": "d1",
                    "name": "Early Blight",
                    "probability": 0.62,
                    "details": {
                        "description": "Fungal disease causing concentric target-spot lesions.",
                        "treatment": {
                            "chemical": ["Chlorothalonil", "Mancozeb"],
                            "prevention": ["Crop rotation", "Remove infected debris"],
                        },
                    },
                },
                {
                    "id": "d2",
                    "name": "Bacterial Spot",
                    "probability": 0.21,
                    "details": {
                        "description": "Bacterial infection causing water-soaked lesions.",
                        "treatment": {
                            "chemical": ["Copper-based bactericide"],
                            "prevention": ["Avoid overhead irrigation", "Use certified disease-free seed"],
                        },
                    },
                },
                {
                    "id": "d3",
                    "name": "Septoria Leaf Spot",
                    "probability": 0.09,
                    "details": {"description": "Fungal leaf spot disease.", "treatment": {}},
                },
            ]
        },
    },
}


def run_scenario(label: str, gpt_result: GPTDiseaseVerification) -> None:
    print(f"\n{'=' * 70}\nSCENARIO: {label}\n{'=' * 70}")

    state = new_state(farmer_id="manual-test-farmer")
    state["uploaded_image"] = "ZmFrZS1pbWFnZS1ieXRlcw=="  # base64 for "fake-image-bytes"

    with (
        patch("app.agents.nodes.disease_detection.identify_disease", return_value=CROP_HEALTH_RAW_RESPONSE),
        patch("app.agents.nodes.disease_detection._vision_llm") as mock_llm,
    ):
        mock_llm.invoke.return_value = gpt_result

        detection_update = disease_detection(state)
        state.update(detection_update)

        explanation_update = disease_explanation(state)
        state.update(explanation_update)

    print("\n--- disease_result ---")
    print(json.dumps(state["disease_result"], indent=2))

    print("\n--- trace_log ---")
    for entry in detection_update["trace_log"]:
        badge = entry.get("badge")
        print(f"[{entry['tool']}] {entry['summary']}" + (f"  badge={badge}" if badge else ""))

    print("\n--- farmer-facing message ---")
    message = explanation_update["messages"][0]
    print(message.content)
    if message.additional_kwargs.get("badge"):
        print(f"\n[UI badge] {message.additional_kwargs['badge']}")


if __name__ == "__main__":
    run_scenario(
        "Sources AGREE (high confidence)",
        GPTDiseaseVerification(
            agrees=True,
            disease_name="Early Blight",
            visual_evidence="concentric target-spot lesions with yellow halos on the older, lower leaves",
            reasoning="The lesion pattern matches the classic Alternaria solani ring structure crop.health flagged.",
            clarifying_question=None,
        ),
    )

    run_scenario(
        "Sources DISAGREE (low confidence)",
        GPTDiseaseVerification(
            agrees=False,
            disease_name="Bacterial Spot",
            visual_evidence="water-soaked lesions with a yellow halo concentrated on new upper growth, no concentric rings",
            reasoning=(
                "The lesions lack the concentric ring pattern typical of early blight, and they're on new "
                "growth rather than older leaves, which points to bacterial spot instead."
            ),
            clarifying_question="Are the spots mostly on the older bottom leaves or the new growth at the top?",
        ),
    )
