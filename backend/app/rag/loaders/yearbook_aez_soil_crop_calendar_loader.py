"""Loader/chunker for the curated "Yearbook of Agricultural Statistics 2020 —
Chapter 1: AEZ, Soil, Crop Calendar" PDF.

Unlike the BARC handbook (free-flowing prose grouped under keyword
headings), this file is a pre-curated, highly regular extract: six
sections (1.3-1.4 AEZ, 1.5 Land Levels, 1.6 Soil Classification, 1.7 Crop
Seasons, 1.8 Crop Calendar, 1.9 Physiography), each introduced by a
"Section 1.x - Title" line. Three of those sections are themselves lists
of self-contained, fixed-field records: "AEZ-N: Name", "Soil Unit N:
Name", and "N. CropName" (Crop Calendar). Each record is short (well
under the embedding model's token limit) and semantically atomic, so this
loader emits one chunk per record rather than a fixed-size sliding
window - splitting e.g. an AEZ zone's description mid-paragraph would
lose the coherence a retrieval query relies on. Any leading narrative
before the first record in a section (and the whole of the
non-record-list sections 1.5/1.7/1.9) becomes its own single chunk.
"""
import re
from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader

SECTION_HEADER_RE = re.compile(r"^Section\s+[\d.\-]+\s*[—\-–]\s*(.+)$")
AEZ_HEADER_RE = re.compile(r"^AEZ-\d+:\s*.+$")
SOIL_UNIT_HEADER_RE = re.compile(r"^Soil Unit \d+:\s*.+$")
CROP_HEADER_RE = re.compile(r"^\d{1,3}\.\s*(.+?)\s*:?$")

# Keys are matched against the lowercased section title captured by
# SECTION_HEADER_RE; values are the human-readable topic stored on each
# chunk. Order doesn't matter - titles are distinct substrings.
SECTION_TOPIC_KEYWORDS: dict[str, str] = {
    "agro-ecological zones": "Agro-Ecological Zones (AEZ) of Bangladesh",
    "land levels": "Land Levels in Relation to Flooding",
    "soil classification": "Soil Classification of Bangladesh",
    "crop seasons": "Crop Seasons and Seed Requirements",
    "crop calendar": "Crop Calendar of Bangladesh",
    "physiography": "Physiography of Bangladesh",
}

# Sections whose records should each become their own chunk.
RECORD_LIST_TOPICS = {
    "Agro-Ecological Zones (AEZ) of Bangladesh",
    "Soil Classification of Bangladesh",
    "Crop Calendar of Bangladesh",
}

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


def _topic_for_section_title(title: str) -> str | None:
    lowered = title.lower()
    for keyword, topic in SECTION_TOPIC_KEYWORDS.items():
        if keyword in lowered:
            return topic
    return None


def load_and_chunk(pdf_path: str | Path) -> list[Chunk]:
    pages = extract_pages(pdf_path)

    chunks: list[Chunk] = []
    current_topic: str | None = None
    current_section_heading: str | None = None
    current_entry_heading: str | None = None
    current_crop: str | None = None
    buffer_lines: list[str] = []
    buffer_start_page: int | None = None

    def flush() -> None:
        nonlocal buffer_lines, buffer_start_page
        text = " ".join(l.strip() for l in buffer_lines if l.strip())
        buffer_lines = []
        if text:
            chunks.append(
                Chunk(
                    content=text,
                    crop=current_crop,
                    topic=current_topic or DOCUMENT_OVERVIEW_TOPIC,
                    section_heading=current_entry_heading or current_section_heading,
                    page_number=buffer_start_page,
                )
            )
        buffer_start_page = None

    for page_number, text in pages:
        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue

            section_match = SECTION_HEADER_RE.match(stripped)
            if section_match:
                flush()
                current_topic = _topic_for_section_title(section_match.group(1))
                current_section_heading = stripped
                current_entry_heading = None
                current_crop = None
                buffer_start_page = page_number
                buffer_lines.append(stripped)
                continue

            if current_topic in RECORD_LIST_TOPICS:
                if current_topic == "Agro-Ecological Zones (AEZ) of Bangladesh" and AEZ_HEADER_RE.match(stripped):
                    flush()
                    current_entry_heading = stripped
                    current_crop = None
                    buffer_start_page = page_number
                    buffer_lines.append(stripped)
                    continue
                if current_topic == "Soil Classification of Bangladesh" and SOIL_UNIT_HEADER_RE.match(stripped):
                    flush()
                    current_entry_heading = stripped
                    current_crop = None
                    buffer_start_page = page_number
                    buffer_lines.append(stripped)
                    continue
                if current_topic == "Crop Calendar of Bangladesh":
                    crop_match = CROP_HEADER_RE.match(stripped)
                    if crop_match:
                        flush()
                        current_entry_heading = stripped
                        current_crop = crop_match.group(1).strip()
                        buffer_start_page = page_number
                        buffer_lines.append(stripped)
                        continue

            if buffer_start_page is None:
                buffer_start_page = page_number
            buffer_lines.append(stripped)

    flush()
    return chunks
