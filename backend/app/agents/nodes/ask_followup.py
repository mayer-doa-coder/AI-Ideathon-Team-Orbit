from langchain_core.messages import AIMessage

from app.agents.state import AgentState

FIELD_QUESTIONS = {
    "location": "First, where's your farm located? (district or upazila in Bangladesh)",
    "acres": "How many acres are you farming?",
    "soil_type": "What's your soil type — sandy, clay, loamy, or silty?",
    "water_availability": "How would you rate your water availability — low, medium, or high?",
    "budget": "What's your budget for this season, in BDT?",
    "season": "Which season are you planning for — Winter, Summer, Monsoon (Rainy), or Autumn?",
}
FIELD_ORDER = ["location", "acres", "soil_type", "water_availability", "budget", "season"]


def ask_followup(state: AgentState) -> dict:
    missing = state.get("missing_fields") or []
    next_field = next((f for f in FIELD_ORDER if f in missing), missing[0] if missing else None)
    question = FIELD_QUESTIONS.get(next_field, "Could you tell me more about your farm?")

    return {
        "turn_complete": True,
        "messages": [AIMessage(content=question)],
    }
