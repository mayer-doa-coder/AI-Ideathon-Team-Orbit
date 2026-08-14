"""Loader/chunker for the curated "Fertilizer Recommendation Guide-2018
(BARC)" embeddings-ready extraction.

Unlike the other curated PDFs in this knowledge base, the FRG-2018 source
is a 233-page *scanned* document with no text layer, so this extract is
OCR output (Tesseract 5), not hand-verified prose. The preparer already
tagged every original source page with its own
"[Source: FRG-2018, p.N] [OK]" or "[Source: FRG-2018, p.N] [VERIFY]"
marker - [OK] for high-confidence narrative OCR, [VERIFY] for
numeric/dose tables that were run through a second OCR pass plus
column-position reconstruction because the scan's real resolution
(~72 DPI) is below what small-numeral OCR needs reliably; the two OCR
passes disagreed with each other on every dense table page tested.

Two consequences for chunking, both different from the AEZ/Soil Atlas
loaders:

1. The atomic unit is the tagged block, not a pypdf page - one
   `[Source: FRG-2018, p.N]` marker always starts exactly one original
   source page's text, but several original pages can land on the same
   extraction-PDF page. Splitting on the marker (221 of them) gives exact,
   citation-accurate page numbers for free; splitting on pypdf pages
   would not.
2. No table-cell reconstruction is attempted for [VERIFY] pages (contrast
   with soil_atlas_loader.py). Spot-checking the fertilizer-dose tables
   shows OCR'd digits that are visibly wrong or inconsistent row-to-row
   (varying column counts, letters substituted for digits) - exactly the
   unreliability the source document warns about. Forcing those numbers
   into a clean structure would fabricate precision that isn't there.
   Instead the [VERIFY]/"verify against source page" text that the
   preparer already put at the top of every such block is left in place
   as the caveat, since KBChunk has no confidence column and this repo
   deliberately isn't adding one for a single loader.

Chapter (topic) and, within Chapter 11 ("Fertilizer Recommendation for
Crops"), crop (crop) tracking are both best-effort: chapter headings are
matched against a closed whitelist of the exact strings verified to occur
in this document's body text (an open-ended "line that looks like a
heading" regex was tried first and matched OCR garbage like "9 RIVER
PLOX" from a mangled table - a closed whitelist can't do that). Any page
whose heading isn't recognized just keeps the previous chapter's/crop's
label rather than getting mislabeled.
"""
import re
from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader

PAGE_TAG_RE = re.compile(r"^\[Source: FRG-2018, p\.(\d+)\] \[(OK|VERIFY)\](.*)$")

# Exact body-heading strings, verified against the extracted text, mapped
# to a canonical topic label. Deliberately a closed whitelist rather than
# an open-ended regex - see module docstring.
CHAPTER_HEADINGS: dict[str, str] = {
    "1. INTRODUCTION": "1. Introduction",
    "2. PLANT NUTRIENTS": "2. Plant Nutrients",
    "3. MINERALOGY AND SOIL FERTILITY STATUS OF DIFFERENT AEZs": "3. Mineralogy and Soil Fertility Status of Different AEZs",
    "4. SOIL FERTILITY EVALUATION": "4. Soil Fertility Evaluation",
    "5. FERTILIZERS AND THEIR USE": "5. Fertilizers and Their Use",
    "6. SOIL ORGANIC MATTER MANAGEMENT": "6. Soil Organic Matter Management",
    "7. SOIL ACIDITY AND LIMING": "7. Soil Acidity and Liming",
    "8. FERTILIZER MANAGEMENT FOR DIFFERENT FARMING SYSTEMS": "8. Fertilizer Management for Different Farming Systems",
    "9. FERTILIZER MANAGEMENT IN DEGRADED LAND FARMING": "9. Fertilizer Management in Degraded Land Farming",
    "9, FERTILIZER MANAGEMENT IN DEGRADED LAND FARMING": "9. Fertilizer Management in Degraded Land Farming",
    "10. QUALITY CONTROL OF FERTILIZERS": "10. Quality Control of Fertilizers",
    "11. FERTILIZER RECOMMENDATION FOR CROPS": "11. Fertilizer Recommendation for Crops",
    "11 FERTILIZER RECOMMENDATION FOR CROPS": "11. Fertilizer Recommendation for Crops",
}

CHAPTER_11_TOPIC = "11. Fertilizer Recommendation for Crops"

# Matches the "CROP NAME (Genus species)" headings used throughout
# Chapter 11 (e.g. "RICE (Oryza sativa L.)", "WHEAT (Triticum aestivum)").
# Verified against the full document: 131 matches, all genuine crop
# headings, no false positives - but still gated to Chapter 11 only
# (see load_and_chunk) as a second layer of safety.
CROP_HEADING_RE = re.compile(r"^[A-Z][A-Z .,'&/-]{1,45}\([A-Z][a-zA-Z.,&\- ]+\)\.?$")

DOCUMENT_OVERVIEW_TOPIC = "Document Overview"


class Chunk(TypedDict):
    content: str
    crop: str | None
    topic: str | None
    section_heading: str | None
    page_number: int | None


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RUN_RE = re.compile(r"[ \t]{2,}")


def _clean_page_text(text: str) -> str:
    text = _CONTROL_CHARS_RE.sub(" ", text)
    text = _WHITESPACE_RUN_RE.sub(" ", text)
    return text


def extract_pages(pdf_path: str | Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    return [(i + 1, _clean_page_text(page.extract_text() or "")) for i, page in enumerate(reader.pages)]


def _crop_name_from_heading(heading: str) -> str:
    name = heading.split("(")[0].strip()
    return name.title().replace("'S", "'s")


def load_and_chunk(pdf_path: str | Path) -> list[Chunk]:
    pages = extract_pages(pdf_path)

    chunks: list[Chunk] = []
    current_topic: str | None = None
    current_topic_raw: str | None = None
    current_crop: str | None = None
    current_source_page: int | None = None
    buffer_lines: list[str] = []

    def flush() -> None:
        nonlocal buffer_lines
        text = " ".join(l.strip() for l in buffer_lines if l.strip())
        buffer_lines = []
        if text:
            chunks.append(
                Chunk(
                    content=text,
                    crop=current_crop,
                    topic=current_topic or DOCUMENT_OVERVIEW_TOPIC,
                    section_heading=current_crop or current_topic_raw,
                    page_number=current_source_page,
                )
            )

    for _pypdf_page_number, text in pages:
        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue

            tag_match = PAGE_TAG_RE.match(stripped)
            if tag_match:
                flush()
                current_source_page = int(tag_match.group(1))
                buffer_lines.append(stripped)
                continue

            if stripped in CHAPTER_HEADINGS:
                current_topic = CHAPTER_HEADINGS[stripped]
                current_topic_raw = stripped
                current_crop = None
                buffer_lines.append(stripped)
                continue

            if current_topic == CHAPTER_11_TOPIC and CROP_HEADING_RE.match(stripped):
                current_crop = _crop_name_from_heading(stripped)
                buffer_lines.append(stripped)
                continue

            buffer_lines.append(stripped)

    flush()
    return chunks
