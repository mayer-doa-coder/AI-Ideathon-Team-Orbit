"""knowledge_retrieval — pulls the agronomy passages that crop_recommendation
reasons over, as its own graph node so it can run *concurrently* with
weather_tool instead of after it.

This used to be the first half of crop_recommendation. Splitting it out is what
makes the fan-out in graph_conversation.py possible: retrieval only needs the
farm profile (soil, season), and the forecast only needs the location, so
neither waits on the other. They are the two slowest steps before a crop
recommendation can be made — an embedding + pgvector query, and a geocode plus
an Open-Meteo round trip — and running them together removes roughly one of
them from the farmer's wait.

Writes `retrieved_docs` and `trace_log`; weather_tool writes `weather_data` and
`farm_profile`. The two share no state key except `trace_log`, which has an
`operator.add` reducer (state.py), so their concurrent updates merge instead of
colliding — that disjointness is what makes the parallel branch safe, and it is
the thing to preserve if either node grows new outputs.
"""
from app.agents.state import AgentState
from app.db.session import SessionLocal
from app.tools.rag import is_grounded_enough, retrieve_agri_knowledge
from app.tools.web_search import web_search_as_docs

RETRIEVAL_TOP_K = 6


def build_crop_query(profile: dict) -> str:
    """Shared with crop_recommendation's trace so the query shown in the trace
    panel is the one that actually ran."""
    return (
        f"suitable crop varieties for {profile.get('soil_type', '')} soil "
        f"in {profile.get('season', '')} season Bangladesh"
    )


def knowledge_retrieval(state: AgentState) -> dict:
    profile = state.get("farm_profile") or {}
    query = build_crop_query(profile)

    db = SessionLocal()
    try:
        docs = retrieve_agri_knowledge(db, query, k=RETRIEVAL_TOP_K)
    finally:
        db.close()

    trace = [
        {
            "type": "knowledge",
            "tool": "retrieve_agri_knowledge",
            "paramsDisplay": f'query="{query}"',
            "params": {"query": query, "top_k": RETRIEVAL_TOP_K},
            "response": {
                "chunks_retrieved": len(docs),
                "sources": sorted({d["source_title"] for d in docs}),
                "top_chunk": docs[0]["content"][:280] if docs else None,
            },
            "summary": f"{len(docs)} chunks retrieved from the knowledge base",
        }
    ]

    if not is_grounded_enough(docs):
        # Knowledge base had nothing relevant for this soil/season
        # combination — fall back to a real web search rather than let the
        # LLM reason from unrooted general knowledge.
        docs = web_search_as_docs(query, max_results=RETRIEVAL_TOP_K)
        trace.append(
            {
                "type": "knowledge",
                "tool": "web_search",
                "paramsDisplay": f'query="{query}"',
                "params": {"query": query},
                "response": {
                    "chunks_retrieved": len(docs),
                    "urls": [d["url"] for d in docs if d.get("url")],
                },
                "summary": f"knowledge base had nothing — {len(docs)} web results used instead",
            }
        )

    return {"trace_log": trace, "retrieved_docs": docs}
