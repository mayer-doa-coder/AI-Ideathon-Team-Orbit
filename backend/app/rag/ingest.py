from pathlib import Path

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import KBChunk
from app.rag.loaders.barc_handbook_loader import load_and_chunk

EMBEDDING_BATCH_SIZE = 100


def _embed_texts(client: OpenAI, texts: list[str], model: str) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(model=model, input=batch)
        embeddings.extend(item.embedding for item in response.data)
    return embeddings


def ingest_pdf(pdf_path: str | Path, source_title: str, db: Session) -> int:
    chunks = load_and_chunk(pdf_path)
    if not chunks:
        return 0

    db.query(KBChunk).filter(KBChunk.source_title == source_title).delete()
    db.commit()

    client = OpenAI(api_key=settings.openai_api_key)
    texts = [chunk["content"] for chunk in chunks]
    embeddings = _embed_texts(client, texts, settings.embedding_model)

    rows = [
        KBChunk(
            source_title=source_title,
            crop=chunk["crop"],
            topic=chunk["topic"],
            section_heading=chunk["section_heading"],
            page_number=chunk["page_number"],
            content=chunk["content"],
            embedding=embedding,
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    db.add_all(rows)
    db.commit()
    return len(rows)
