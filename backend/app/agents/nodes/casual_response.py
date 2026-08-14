from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.core.config import settings

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "casual_response.md"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

_llm = ChatOpenAI(model=settings.chat_model, temperature=0.5, api_key=settings.openai_api_key)


def casual_response(state: AgentState) -> dict:
    # .stream() (not .invoke()) so this is a genuine token-by-token generator —
    # LangGraph's stream_mode="messages" otherwise has to synthesize a final
    # full-text chunk on top of the real deltas when the underlying call is a
    # single .invoke(), which duplicates the message for SSE token consumers.
    full_text = "".join(
        chunk.content
        for chunk in _llm.stream([{"role": "system", "content": _SYSTEM_PROMPT}, *state["messages"][-4:]])
    )
    return {"turn_complete": True, "messages": [AIMessage(content=full_text)]}
