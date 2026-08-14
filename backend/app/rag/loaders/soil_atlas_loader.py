"""Loader/chunker for the curated "Soil Fertility Atlas Bangladesh 2020"
PDF extract.

The file has two very different regions: three plain narrative sections
(Prologue, Background, Methodology - each just a bare heading line, no
"Section N -" prefix like the Yearbook extract), followed by 12 national
soil-fertility status tables. Critically, pypdf extracts each table as a
flat stream of bare cell values with no key:value labels at all - e.g.
"Very Low to Low" / "4,316,455" / "50.27" appear as three consecutive
lines with nothing marking which is the class, which is the area, and
which is the percentage. Every table is a rigid 3-column grid though
(Fertility/Status Class, Area (ha), % of Arable Land), so once the three
column-header lines are located, the remaining lines can be regrouped
into triplets and re-labelled unambiguously.

Each whole table becomes exactly one chunk (not one chunk per row): a
lone row like "Medium / 5,082,396 / 59.19" is meaningless without the
table it came from (which nutrient? which soil/crop scope?), so the
table - not the row - is this document's atomic semantic unit, the same
reasoning that made a whole AEZ zone the atomic unit in the Yearbook
loader.
"""
import re
from pathlib import Path
from typing import TypedDict

from pypdf import PdfReader

NARRATIVE_HEADINGS = {"Prologue", "Background", "Methodology"}
TABLES_SECTION_HEADING = "National Soil Fertility Status Tables (2020)"
TABLE_HEADER_RE = re.compile(r"^Table \d+\s*[—\-–]\s*.+$")
COLUMN_HEADER_LABELS = ("Fertility / Status Class", "Area (ha)", "% of Arable Land")
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


def _build_table_content(lines: list[str]) -> str:
    """Reconstruct one table's chunk text from its raw extracted lines.

    `lines[0]` is the "Table N - Name" header line; everything after it is
    an optional subtitle (e.g. "Loamy to Clayey Soils of Wetland Rice
    Crops"), then the three column-header labels, then data rows as flat
    triplets, then a "[Source: ...]" citation (which may wrap onto a
    second line with no leading "["). Raises ValueError if the expected
    column-header/triplet shape isn't found, rather than silently
    mis-pairing numbers to the wrong class.
    """
    header_line = lines[0]
    rest = lines[1:]

    try:
        col1_idx = rest.index(COLUMN_HEADER_LABELS[0])
    except ValueError as exc:
        raise ValueError(f"Could not find column headers in table starting with {header_line!r}") from exc

    if rest[col1_idx : col1_idx + 3] != list(COLUMN_HEADER_LABELS):
        raise ValueError(
            f"Unexpected column header sequence in table starting with {header_line!r}: "
            f"{rest[col1_idx : col1_idx + 3]!r}"
        )

    subtitle_lines = rest[:col1_idx]
    data_lines = rest[col1_idx + 3 :]

    parts = [header_line, *subtitle_lines, "Columns: Fertility/Status Class, Area (ha), % of Arable Land."]

    row_cells: list[str] = []
    trailing: list[str] = []
    in_citation = False
    for line in data_lines:
        if not in_citation and line.upper().startswith("[SOURCE:"):
            in_citation = True
        if in_citation:
            trailing.append(line)
            continue
        row_cells.append(line)
        if len(row_cells) == 3:
            cls, area, pct = row_cells
            parts.append(f"{cls} — Area: {area} ha, % of Arable Land: {pct}")
            row_cells = []

    if row_cells:
        raise ValueError(f"Leftover incomplete data row in table starting with {header_line!r}: {row_cells!r}")

    if trailing:
        parts.append(" ".join(trailing))

    return " ".join(parts)


def load_and_chunk(pdf_path: str | Path) -> list[Chunk]:
    pages = extract_pages(pdf_path)

    chunks: list[Chunk] = []
    current_topic: str | None = None
    current_section_heading: str | None = None
    current_entry_heading: str | None = None
    in_tables_section = False
    is_table_entry = False
    buffer_lines: list[str] = []
    buffer_start_page: int | None = None

    def flush() -> None:
        nonlocal buffer_lines, buffer_start_page, is_table_entry
        if not buffer_lines:
            buffer_start_page = None
            is_table_entry = False
            return

        content = _build_table_content(buffer_lines) if is_table_entry else " ".join(
            l.strip() for l in buffer_lines if l.strip()
        )
        buffer_lines = []
        if content:
            chunks.append(
                Chunk(
                    content=content,
                    crop=None,
                    topic=current_topic or DOCUMENT_OVERVIEW_TOPIC,
                    section_heading=current_entry_heading or current_section_heading,
                    page_number=buffer_start_page,
                )
            )
        buffer_start_page = None
        is_table_entry = False

    for page_number, text in pages:
        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue

            if stripped in NARRATIVE_HEADINGS:
                flush()
                current_topic = stripped
                current_section_heading = stripped
                current_entry_heading = None
                in_tables_section = False
                buffer_start_page = page_number
                buffer_lines.append(stripped)
                continue

            if stripped == TABLES_SECTION_HEADING:
                flush()
                current_topic = TABLES_SECTION_HEADING
                current_section_heading = stripped
                current_entry_heading = None
                in_tables_section = True
                buffer_start_page = page_number
                buffer_lines.append(stripped)
                continue

            if in_tables_section and TABLE_HEADER_RE.match(stripped):
                flush()
                current_entry_heading = stripped
                is_table_entry = True
                buffer_start_page = page_number
                buffer_lines.append(stripped)
                continue

            if buffer_start_page is None:
                buffer_start_page = page_number
            buffer_lines.append(stripped)

    flush()
    return chunks
