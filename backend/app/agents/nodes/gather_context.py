"""gather_context — the fan-out point where the conversation graph stops
working one step at a time.

It does no work itself. LangGraph fans out by giving a single node more than
one outgoing edge, and a conditional edge can only name one destination, so the
supervisor router needs something to point at that then splits. That is this
node's entire job.

    classify_intent ──(router)──► gather_context
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
                   weather_parallel    knowledge_retrieval
                          │                   │
                          └─────────┬─────────┘
                                    ▼
                          crop_recommendation   (join)

The two branches are genuinely independent: the forecast needs only the
location, retrieval needs only soil and season, and neither reads the other's
output. crop_recommendation is the join — LangGraph runs it once, after both
branches have completed, and by then both `weather_data` and `retrieved_docs`
are in state.

The safety property that makes this sound is that the branches write disjoint
state keys — weather writes `weather_data`/`farm_profile`, retrieval writes
`retrieved_docs` — and the one key they share, `trace_log`, is declared with an
`operator.add` reducer in state.py so concurrent appends merge. If either
branch grows a new output, check it against the other before adding it, or
LangGraph will raise InvalidUpdateError on the concurrent write.
"""
from app.agents.state import AgentState


def gather_context(state: AgentState) -> dict:
    return {}
