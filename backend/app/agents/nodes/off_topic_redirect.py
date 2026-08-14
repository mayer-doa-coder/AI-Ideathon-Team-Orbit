from langchain_core.messages import AIMessage

from app.agents.state import AgentState

MESSAGE = (
    "I'm focused on helping you plan your farming season — crop choice, weather, "
    "fertilizer, and finances. Ask me something about your farm and I'll help out!"
)


def off_topic_redirect(state: AgentState) -> dict:
    return {"turn_complete": True, "messages": [AIMessage(content=MESSAGE)]}
