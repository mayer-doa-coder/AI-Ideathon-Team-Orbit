from langchain_core.messages import AIMessage

from app.agents.state import AgentState

MESSAGE = (
    "You don't have a season plan yet, so there's nothing to simulate against. "
    "Let's finish building your plan first, then I can run what-if scenarios for you."
)


def scenario_blocked(state: AgentState) -> dict:
    return {"turn_complete": True, "messages": [AIMessage(content=MESSAGE)]}
