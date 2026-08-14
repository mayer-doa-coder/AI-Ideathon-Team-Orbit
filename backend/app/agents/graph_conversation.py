from langgraph.graph import END, StateGraph

from app.agents.checkpointer import checkpointer
from app.agents.nodes.ask_followup import ask_followup
from app.agents.nodes.calculate_financials import calculate_financials
from app.agents.nodes.casual_response import casual_response
from app.agents.nodes.classify_intent import classify_intent
from app.agents.nodes.core_change_handler import core_change_handler
from app.agents.nodes.crop_recommendation import crop_recommendation
from app.agents.nodes.load_memory import load_memory
from app.agents.nodes.disease_detection import disease_detection
from app.agents.nodes.disease_explanation import disease_explanation
from app.agents.nodes.market_price_lookup import market_price_lookup
from app.agents.nodes.marketplace_lookup import marketplace_lookup
from app.agents.nodes.off_topic_redirect import off_topic_redirect
from app.agents.nodes.persist import persist
from app.agents.nodes.qa_agent import qa_agent
from app.agents.nodes.scenario_blocked import scenario_blocked
from app.agents.nodes.scenario_handler import scenario_handler
from app.agents.nodes.season_planner import season_planner
from app.agents.nodes.voice_input import voice_input
from app.agents.nodes.voice_output import voice_output
from app.agents.nodes.weather_tool import weather_tool
from app.agents.router import intake_router, supervisor_router, voice_input_router
from app.agents.state import AgentState

builder = StateGraph(AgentState)

builder.add_node("load_memory", load_memory)
builder.add_node("classify_intent", classify_intent)
builder.add_node("core_change_handler", core_change_handler)
builder.add_node("ask_followup", ask_followup)
builder.add_node("weather_tool", weather_tool)
builder.add_node("crop_recommendation", crop_recommendation)
builder.add_node("disease_detection", disease_detection)
builder.add_node("disease_explanation", disease_explanation)
builder.add_node("voice_input", voice_input)
builder.add_node("voice_output", voice_output)
builder.add_node("season_planner", season_planner)
builder.add_node("calculate_financials", calculate_financials)
builder.add_node("qa_agent", qa_agent)
builder.add_node("casual_response", casual_response)
builder.add_node("off_topic_redirect", off_topic_redirect)
builder.add_node("scenario_handler", scenario_handler)
builder.add_node("scenario_blocked", scenario_blocked)
builder.add_node("marketplace_lookup", marketplace_lookup)
builder.add_node("market_price_lookup", market_price_lookup)
builder.add_node("persist", persist)

builder.set_entry_point("load_memory")
builder.add_conditional_edges(
    "load_memory",
    intake_router,
    {"disease_detection": "disease_detection", "voice_input": "voice_input", "classify_intent": "classify_intent"},
)
builder.add_conditional_edges(
    "voice_input",
    voice_input_router,
    {"classify_intent": "classify_intent", "voice_output": "voice_output"},
)

ROUTE_MAP = {
    "core_change_handler": "core_change_handler",
    "ask_followup": "ask_followup",
    "weather_tool": "weather_tool",
    "crop_recommendation": "crop_recommendation",
    "season_planner": "season_planner",
    "qa_agent": "qa_agent",
    "casual_response": "casual_response",
    "off_topic_redirect": "off_topic_redirect",
    "scenario_handler": "scenario_handler",
    "scenario_blocked": "scenario_blocked",
    "marketplace_lookup": "marketplace_lookup",
    "market_price_lookup": "market_price_lookup",
    # Every turn — voice or typed — funnels through voice_output before
    # ending; it no-ops immediately unless state.voice_input.used is true.
    # See nodes/voice_output.py.
    "end": "voice_output",
}

builder.add_conditional_edges("classify_intent", supervisor_router, ROUTE_MAP)
builder.add_conditional_edges("weather_tool", supervisor_router, ROUTE_MAP)
# core_change_handler either ends the turn (asked a question / declined
# replan) or continues with turn_complete=False after a "yes" — same
# re-entry pattern as weather_tool, letting the router send it on into
# weather_tool -> crop_recommendation from a cleared-out state.
builder.add_conditional_edges("core_change_handler", supervisor_router, ROUTE_MAP)

builder.add_edge("ask_followup", "voice_output")
builder.add_edge("crop_recommendation", "voice_output")
builder.add_edge("disease_detection", "disease_explanation")
builder.add_edge("disease_explanation", "voice_output")
builder.add_edge("season_planner", "calculate_financials")
builder.add_edge("calculate_financials", "persist")
builder.add_edge("persist", "voice_output")
builder.add_edge("qa_agent", "voice_output")
builder.add_edge("casual_response", "voice_output")
builder.add_edge("off_topic_redirect", "voice_output")
builder.add_edge("scenario_handler", "voice_output")
builder.add_edge("scenario_blocked", "voice_output")
builder.add_edge("marketplace_lookup", "voice_output")
builder.add_edge("market_price_lookup", "voice_output")
builder.add_edge("voice_output", END)

conversation_graph = builder.compile(checkpointer=checkpointer)
