"""CLI to (re)build the knowledge base from the curated Soil Fertility
Atlas Bangladesh 2020 extract (Prologue, Background, Methodology, and the
12 national soil-fertility status tables).

This mirrors run_ingestion.py's embed-and-store logic but uses the
document-specific soil_atlas_loader instead of the BARC handbook loader,
since the two source PDFs have unrelated internal structures. Kept as a
separate script (rather than parameterizing ingest_pdf/run_ingestion.py
with a loader argument) so the existing BARC ingestion path is left
untouched.

Usage (from /app inside the backend container, or the backend/ venv):
    python -m scripts.ingest_soil_fertility_atlas
    python -m scripts.ingest_soil_fertility_atlas --source path/to/other.pdf --title "Other Title"
"""
import argparse
from pathlib import Path

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import KBChunk
from app.db.session import SessionLocal
from app.rag.loaders.soil_atlas_loader import load_and_chunk

EMBEDDING_BATCH_SIZE = 100

DEFAULT_SOURCE = (
    Path(__file__).resolve().parent.parent.parent
    / "datasets-AgriSense AI"
    / "SoilFertilityAtlas2020_Curated.pdf"
)
DEFAULT_TITLE = "Soil Fertility Atlas Bangladesh 2020 (SRDI)"


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest the Soil Fertility Atlas Bangladesh 2020 PDF into the kb_chunks knowledge base"
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Path to the source PDF")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="source_title stored on each chunk")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        count = ingest_pdf(args.source, args.title, db)
        print(f"Ingested {count} chunks from '{args.source}' as '{args.title}'")
    finally:
        db.close()


if __name__ == "__main__":
    main()
