"""Loader/chunker for the BARC "Hand Book of Agricultural Technology" PDF.

The book is organized as: category (Roman numeral) -> crop (numbered) ->
subsection (e.g. "1.2 Production Technology") -> keyword headings (e.g.
"Seed rate", "Major diseases and control measures:"). Chunking walks the
extracted text line by line, tracks the current crop/section from these
headings, and groups body text under them so each chunk stays topically
coherent instead of being a fixed-size window.
"""
import re
from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader

ROMAN_CATEGORY_RE = re.compile(r"^[IVXLC]{1,6}\.\s+[A-Z][A-Z \-&/]{2,60}$")
CROP_HEADER_RE = re.compile(r"^\d{1,2}\.\s+([A-Z][A-Za-z0-9 /()\-]{1,60})$")
SUBSECTION_RE = re.compile(r"^\d{1,2}\.\d{1,2}\s+([A-Za-z][A-Za-z /\-]{2,60})$")

KEYWORD_HEADINGS = {
    "land and soil", "land andsoil", "climate, land and soil", "climate and soil",
    "seed rate", "seed treatment", "time of sowing", "time of planting",
    "sowing method", "seedbed preparation", "seed bed preparation",
    "land preparation", "transplanting method", "fertilizer application",
    "fertilizer dose and application method", "fertilizer dose and application methods",
    "irrigation", "intercultural operation", "pest management",
    "major diseases and control measures", "major insects and control measures",
    "major diseases and control measure", "major insects and control measure",
    "control measures", "harvesting and seed preservation",
    "harvesting and fruit preservation", "seed preservation", "production technology",
    "varieties", "spacing", "pit preparation", "nursery bed preparation",
}

MIN_CHUNK_CHARS = 40
MAX_CHUNK_CHARS = 1000
CHUNK_OVERLAP_CHARS = 150


class Chunk(TypedDict):
    content: str
    crop: str | None
    topic: str | None
    section_heading: str | None
    page_number: int | None


def _is_keyword_heading(line: str) -> bool:
    return len(line) < 80 and line.rstrip(":").strip().lower() in KEYWORD_HEADINGS


def _classify_heading(line: str) -> tuple[str, str] | None:
    """Return (kind, label) if the line is a heading, else None."""
    stripped = line.strip()
    if not stripped:
        return None
    if ROMAN_CATEGORY_RE.match(stripped):
        return "category", stripped
    match = CROP_HEADER_RE.match(stripped)
    if match:
        return "crop", match.group(1).strip()
    match = SUBSECTION_RE.match(stripped)
    if match:
        return "subsection", match.group(1).strip()
    if _is_keyword_heading(stripped):
        return "keyword", stripped.rstrip(":").strip()
    return None


def _split_long_text(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            pieces.append(current)
        overlap_text = current[-overlap:] if current else ""
        current = f"{overlap_text} {sentence}".strip()
        while len(current) > max_chars * 1.5:
            pieces.append(current[:max_chars])
            current = current[max_chars - overlap:]
    if current:
        pieces.append(current)
    return pieces


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE_RUN_RE = re.compile(r"[ \t]{2,}")


def _clean_page_text(text: str) -> str:
    """Strip stray control-char glyphs (e.g. bullet points that decode as
    0x7f under this PDF's font encoding) and collapse repeated spaces."""
    text = _CONTROL_CHARS_RE.sub(" ", text)
    text = _WHITESPACE_RUN_RE.sub(" ", text)
    return text


def extract_pages(pdf_path: str | Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    return [(i + 1, _clean_page_text(page.extract_text() or "")) for i, page in enumerate(reader.pages)]


def load_and_chunk(pdf_path: str | Path) -> list[Chunk]:
    pages = extract_pages(pdf_path)

    chunks: list[Chunk] = []
    current_crop: str | None = None
    current_topic: str | None = None
    current_section_heading: str | None = None
    buffer_lines: list[str] = []
    buffer_start_page: int | None = None

    def flush() -> None:
        nonlocal buffer_lines, buffer_start_page
        text = " ".join(l.strip() for l in buffer_lines if l.strip())
        buffer_lines = []
        if len(text) < MIN_CHUNK_CHARS:
            buffer_start_page = None
            return
        for piece in _split_long_text(text):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(
                    content=piece,
                    crop=current_crop,
                    topic=current_topic,
                    section_heading=current_section_heading,
                    page_number=buffer_start_page,
                )
            )
        buffer_start_page = None

    for page_number, text in pages:
        for raw_line in text.split("\n"):
            heading = _classify_heading(raw_line)
            if heading is None:
                if raw_line.strip():
                    if buffer_start_page is None:
                        buffer_start_page = page_number
                    buffer_lines.append(raw_line)
                continue

            kind, label = heading
            flush()
            current_section_heading = label
            if kind == "category":
                current_crop = None
                current_topic = label
            elif kind == "crop":
                current_crop = label
                current_topic = None
            elif kind == "subsection":
                current_topic = label
            elif kind == "keyword":
                current_topic = label

    flush()
    return chunks
