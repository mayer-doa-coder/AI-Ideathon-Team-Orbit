"""Linear RAG question-answering: retrieve -> stuff context -> generate.

No conversation state, no history — one question in, one grounded answer out.
This backs the standalone `/api/rag/ask` endpoint only. The conversation
graph's own question-answering (`nodes/qa_agent.py`) is a separate,
genuinely agentic `create_agent` tool-calling loop that decides for itself
whether to call this same retrieval primitive (`tools/rag.py`), a live
weather lookup, the farmer's own dashboard, or the web — it doesn't call
through this linear helper.

Falls back to a real web search (see `tools/web_search.py`) only when the
knowledge base returns zero chunks — the KB stays the primary grounding
path; the web is what happens when a question is genuinely outside what's
been embedded, not a routine substitute for it.
"""
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tools.rag import is_grounded_enough, retrieve_agri_knowledge
from app.tools.web_search import web_search_as_docs

FORMAT_RULES = (
    "Write in plain prose, formatted for a plain-text chat bubble — no markdown at all: "
    "no asterisks, no bold/italic, no headers, no markdown bullet or numbered lists. If you "
    "need to list multiple items, write them as a short sentence or separate them with a dash "
    "and a space on their own line, in plain text."
)

SYSTEM_PROMPT = (
    "You are Green Leaf AI, an agricultural advisor for farmers in Bangladesh. "
    "Answer the user's question using ONLY the reference material provided below, "
    "which is excerpted from BARC's Hand Book of Agricultural Technology. "
    "Be concise and practical, and prefer concrete figures (rates, dosages, "
    "durations) from the material over vague advice. If the reference material "
    "does not contain enough information to answer, say so plainly instead of "
    "guessing or using outside knowledge. " + FORMAT_RULES
)

WEB_SYSTEM_PROMPT = (
    "You are Green Leaf AI, an agricultural advisor for farmers in Bangladesh. "
    "The knowledge base had nothing relevant to this question, so answer using "
    "ONLY the web search results provided below instead. Be concise and "
    "practical, and prefer concrete figures over vague advice. Just answer the "
    "question directly — don't mention the knowledge base, don't explain where "
    "the information came from. If the material still doesn't answer the "
    "question, say so plainly instead of guessing. " + FORMAT_RULES
)

NO_RESULTS_ANSWER = "I couldn't find anything relevant in the knowledge base or the web for that question."


def _build_context(sources: list[dict]) -> str:
    parts = []
    for i, s in enumerate(sources):
        if s.get("url"):
            header = f"[{i + 1}] (web result: {s['url']})"
        else:
            header = f"[{i + 1}] (crop: {s['crop'] or 'general'}, topic: {s['topic'] or 'n/a'}, page {s['page_number']})"
        parts.append(f"{header}\n{s['content']}")
    return "\n\n".join(parts)


def answer_question(db: Session, query: str, k: int = 5) -> dict:
    sources = retrieve_agri_knowledge(db, query, k=k)
    used_web = False

    if not is_grounded_enough(sources):
        sources = web_search_as_docs(query, max_results=k)
        used_web = bool(sources)

    if not sources:
        return {"answer": NO_RESULTS_ANSWER, "sources": [], "used_web": False}

    system_prompt = WEB_SYSTEM_PROMPT if used_web else SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Reference material:\n{_build_context(sources)}\n\nQuestion: {query}",
        },
    ]

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(model=settings.chat_model, messages=messages)

    return {"answer": response.choices[0].message.content, "sources": sources, "used_web": used_web}
