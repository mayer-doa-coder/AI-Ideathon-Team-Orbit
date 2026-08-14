from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import KBChunk

DEFAULT_TOP_K = 5

# A plain top-k cosine search always returns *something*, even when nothing
# in the knowledge base is truly related to the query — it just returns the
# least-dissimilar chunks it has. Observed scores: genuinely on-topic
# matches cluster ~0.58-0.63 for this corpus; off-topic queries (e.g. a
# hydroponics question against an agronomy-extension-manual KB) still
# return ~0.43-0.49. This threshold is what lets callers tell "found
# something relevant" apart from "found the least-irrelevant thing" and
# fall back to a web search instead of grounding an answer on a weak match.
MIN_RELEVANT_SIMILARITY = 0.5


def retrieve_agri_knowledge(
    db: Session,
    query: str,
    k: int = DEFAULT_TOP_K,
    crop: str | None = None,
    topic: str | None = None,
) -> list[dict]:
    """Embed `query` and return the top-k most similar kb_chunks rows.

    Optional `crop`/`topic` do a case-insensitive substring pre-filter before
    ranking by cosine distance. `crop` in particular is often a verbose,
    LLM-generated variety name (e.g. "Maize (Kharif-I hybrid)", "T. Aman
    rice") rather than the simple tag the knowledge base stores (e.g.
    "Maize") — an `ilike` substring match requires the stored tag to
    literally contain that whole string, which it usually won't. Rather
    than silently returning zero chunks (and leaving the season plan
    ungrounded) whenever the filter is too strict, fall back to the
    unfiltered semantic search if the filtered query finds nothing.
    """
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=settings.embedding_model, input=[query])
    query_embedding = response.data[0].embedding

    distance = KBChunk.embedding.cosine_distance(query_embedding)

    def _run(apply_crop_filter: bool, apply_topic_filter: bool):
        q = db.query(KBChunk, distance.label("distance"))
        if crop and apply_crop_filter:
            q = q.filter(KBChunk.crop.ilike(f"%{crop}%"))
        if topic and apply_topic_filter:
            q = q.filter(KBChunk.topic.ilike(f"%{topic}%"))
        return q.order_by(distance).limit(k).all()

    rows = _run(apply_crop_filter=True, apply_topic_filter=True)
    if not rows and (crop or topic):
        rows = _run(apply_crop_filter=False, apply_topic_filter=False)

    return [
        {
            "content": chunk.content,
            "crop": chunk.crop,
            "topic": chunk.topic,
            "section_heading": chunk.section_heading,
            "page_number": chunk.page_number,
            "source_title": chunk.source_title,
            "similarity": round(1 - dist, 4),
        }
        for chunk, dist in rows
    ]


def is_grounded_enough(docs: list[dict]) -> bool:
    """True if `docs` (from `retrieve_agri_knowledge`) has something
    relevant enough to actually ground an answer on. Callers should treat
    `False` the same as an empty result and fall back to web search — see
    `MIN_RELEVANT_SIMILARITY` for why "non-empty" alone isn't enough."""
    return bool(docs) and max(d["similarity"] for d in docs) >= MIN_RELEVANT_SIMILARITY
