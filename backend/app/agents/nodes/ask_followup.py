from langchain_core.messages import AIMessage

from app.agents.state import AgentState

# These are fixed strings rather than LLM output, so they do not adapt to the
# language the farmer wrote or spoke in the way a generated reply would. That
# was very visible once voice input shipped: a farmer speaking Bangla got the
# transcript back correctly and then an English follow-up question. Both
# languages are therefore written out here and picked by state.ui_language.
FIELD_QUESTIONS = {
    "en": {
        "location": "First, where's your farm located? (district or upazila in Bangladesh)",
        "acres": "How many acres are you farming?",
        "soil_type": "What's your soil type — sandy, clay, loamy, or silty?",
        "water_availability": "How would you rate your water availability — low, medium, or high?",
        "budget": "What's your budget for this season, in BDT?",
        "season": "Which season are you planning for — Winter, Summer, Monsoon (Rainy), or Autumn?",
    },
    "bn": {
        "location": "প্রথমে বলুন, আপনার জমি কোথায়? (বাংলাদেশের জেলা বা উপজেলা)",
        "acres": "আপনি কত একর জমিতে চাষ করছেন?",
        "soil_type": "আপনার মাটির ধরন কী — বেলে, এঁটেল, দোআঁশ, নাকি পলি?",
        "water_availability": "আপনার পানির প্রাপ্যতা কেমন — কম, মাঝারি, নাকি বেশি?",
        "budget": "এই মৌসুমের জন্য আপনার বাজেট কত টাকা?",
        "season": "আপনি কোন মৌসুমের জন্য পরিকল্পনা করছেন — শীত, গ্রীষ্ম, বর্ষা, নাকি শরৎ?",
    },
}
FALLBACK_QUESTION = {
    "en": "Could you tell me more about your farm?",
    "bn": "আপনার জমি সম্পর্কে আরেকটু বলবেন?",
}
FIELD_ORDER = ["location", "acres", "soil_type", "water_availability", "budget", "season"]


def ask_followup(state: AgentState) -> dict:
    missing = state.get("missing_fields") or []
    next_field = next((f for f in FIELD_ORDER if f in missing), missing[0] if missing else None)

    lang = state.get("ui_language") if state.get("ui_language") in FIELD_QUESTIONS else "en"
    question = FIELD_QUESTIONS[lang].get(next_field, FALLBACK_QUESTION[lang])

    return {
        "turn_complete": True,
        "messages": [AIMessage(content=question)],
    }
