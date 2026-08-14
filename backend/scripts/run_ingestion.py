"""CLI to (re)build the knowledge base from a source PDF.

Usage (from /app inside the backend container, or the backend/ venv):
    python -m scripts.run_ingestion
    python -m scripts.run_ingestion --source data/raw/other_doc.pdf --title "Other Doc"
"""
import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.rag.ingest import ingest_pdf

DEFAULT_SOURCE = Path(__file__).resolve().parent.parent / "data" / "raw" / "barc_handbook_of_agricultural_technology.pdf"
DEFAULT_TITLE = "Hand Book of Agricultural Technology (BARC, 2013)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a PDF into the kb_chunks knowledge base")
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
