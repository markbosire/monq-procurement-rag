"""Text chunking logic with heading detection and metadata enrichment.

Splits document text into overlapping chunks using RecursiveCharacterTextSplitter,
detects section headings, annotates chunks with heading paths and page numbers,
and computes bounding boxes for visual highlighting.
"""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.services.pdf_extraction import records_for_span, compute_bbox_from_records


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[tuple[str, int]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        add_start_index=True,
    )
    docs: list[Document] = splitter.create_documents([text])
    return [(d.page_content, d.metadata["start_index"]) for d in docs]


def _is_boilerplate(text: str) -> bool:
    lower = text.lower()
    if any(kw in lower for kw in ("p.o. box", "po box", "tel:", "phone:", "email:", "fax:")):
        return True
    if re.search(r"\b(ltd|inc\.|corp|llc)\b", lower):
        return True
    if re.match(r"^[A-Z\s,.'-]{1,6}$", text):
        return True
    return False


def _detect_headings(text: str) -> list[tuple[int, str, int]]:
    """Detect headings in text.

    Returns list of (char_position, heading_text, heading_level) sorted by position.
    Level 0 = ALL-CAPS section titles   (e.g. GENERAL, PART 1 TENDERING PROCEDURE)
    Level 1 = SECTION / ARTICLE / PART  (e.g. SECTION 1. INSTRUCTIONS TO INVESTORS)
    Level 2 = Lettered headings         (e.g. A. GENERAL PROVISIONS)
    Level 3 = Numbered sub-headings     (e.g. 1. Meanings/Definitions)
    """
    lines = text.split("\n")
    raw_headings: list[tuple[int, str, int]] = []
    char_offset = 0

    for line in lines:
        stripped = line.strip()
        line_len = len(stripped)

        if not stripped or line_len < 4:
            char_offset += len(line) + 1
            continue

        if "..." in stripped or "\u2026" in stripped:
            char_offset += len(line) + 1
            continue

        ends_with_colon = stripped.rstrip().endswith(":")
        alpha_chars = sum(c.isalpha() for c in stripped)
        upper_ratio = sum(c.isupper() for c in stripped if c.isalpha()) / max(alpha_chars, 1)
        is_all_caps = upper_ratio > 0.7 and line_len > 5 and alpha_chars > 4

        level = None
        heading_text = stripped

        if re.match(r"^(SECTION|ARTICLE|EXHIBIT|APPENDIX|CLAUSE)\s", stripped, re.IGNORECASE):
            level = 1
        elif re.match(r"^PART\s", stripped, re.IGNORECASE):
            level = 1
        elif re.match(r"^Section\s", stripped):
            level = 3
        elif is_all_caps and not ends_with_colon and not _is_boilerplate(stripped):
            if not re.match(r"^[A-Z]\.\s+(?=[A-Z][a-zA-Z]{2,})", stripped) and not re.match(r"^\d{1,2}\.[\s]", stripped):
                level = 0
        if level is None:
            if re.match(r"^[A-Z]\.\s+(?=[A-Z][a-zA-Z]{2,})", stripped):
                level = 2
            elif re.match(r"^\d{1,3}\.[\s]", stripped):
                level = 3

        if level is not None:
            raw_headings.append((char_offset, heading_text, level))

        char_offset += len(line) + 1

    merged: list[tuple[int, str, int]] = []
    for pos, text, level in raw_headings:
        if level == 0 and merged and level == merged[-1][2] and (pos - merged[-1][0]) < 300:
            merged[-1] = (merged[-1][0], merged[-1][1] + " " + text, level)
            continue
        merged.append((pos, text, level))

    filtered: list[tuple[int, str, int]] = []
    for pos, text, level in merged:
        if level == 0 and len(text) < 5:
            continue
        filtered.append((pos, text, level))

    return filtered


def _heading_path_for_position(
    headings: list[tuple[int, str, int]], char_pos: int
) -> str:
    """Build heading path string active at character position char_pos."""
    active: dict[int, str] = {}
    for pos, text, level in headings:
        if pos > char_pos:
            break
        active[level] = text
        for l in list(active.keys()):
            if l > level:
                del active[l]
    parts = [active[l] for l in sorted(active)]
    return " > ".join(parts)


def _build_page_offset_map(page_texts: list[str]) -> list[tuple[int, int]]:
    offsets: list[tuple[int, int]] = []
    offset = 0
    for i, pt in enumerate(page_texts):
        page_len = len(pt)
        offsets.append((offset, offset + page_len))
        offset += page_len + 2
    return offsets


def _page_numbers_for_offsets(
    chunk_start: int,
    chunk_end: int,
    page_offsets: list[tuple[int, int]],
) -> list[int]:
    pages: set[int] = set()
    for page_idx, (p_start, p_end) in enumerate(page_offsets):
        if chunk_start < p_end and chunk_end > p_start:
            pages.add(page_idx + 1)
    return sorted(pages)


def _compute_chunk_bbox(
    chunk_base_text: str,
    page_numbers: list[int],
    page_spans: list[list[dict]],
) -> list[dict]:
    match_text = chunk_base_text.strip()
    heading_match = re.match(r'^\[.*?\]\s+(.*)', match_text)
    if heading_match:
        match_text = heading_match.group(1)
    if not match_text:
        return []

    bboxes: list[dict] = []
    for pn in page_numbers:
        if pn < 1 or pn > len(page_spans):
            continue
        for sp in page_spans[pn - 1]:
            sp_text = sp.get("text", "").strip()
            if sp_text and sp_text in match_text:
                bboxes.append({"page": pn, "x0": sp["x0"], "y0": sp["y0"], "x1": sp["x1"], "y1": sp["y1"]})
    return bboxes


def chunk_text(
    text: str,
    page_texts: list[str] | None = None,
    raw_page_texts: list[str] | None = None,
    page_spans: list[list[dict]] | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    line_records: list | None = None,
    offset_index: list[tuple[int, int, object]] | None = None,
) -> list[tuple[str, list[int], int, int, list[dict]]]:
    """Chunk text with heading enrichment, page-number annotation, char offsets, and bbox.

    Args:
        text: Full cleaned document text.
        page_texts: Per-page cleaned texts (used for page-number inference without line_records).
        raw_page_texts: Per-page raw texts (unused, retained for API compatibility).
        page_spans: Per-page span data for bbox matching.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Character overlap between consecutive chunks.
        line_records: LineRecord list for precise offset-based page-number and bbox computation.
        offset_index: Pre-built (start, end, LineRecord) index.

    Returns:
        List of (chunk_text, page_numbers, char_start, char_end, bbox_list) tuples.
    """
    headings = _detect_headings(text)
    raw_chunks = _split_text(text, chunk_size, chunk_overlap)

    if page_texts and not offset_index:
        page_offsets = _build_page_offset_map(page_texts)
    else:
        page_offsets = []

    result: list[tuple[str, list[int], int, int, list[dict]]] = []
    for chunk_text_content, start_index in raw_chunks:
        chunk_stripped = chunk_text_content.strip()
        if not chunk_stripped:
            continue
        cs = start_index
        ce = start_index + len(chunk_text_content)

        pages: list[int] = []
        bbox: list[dict] = []
        if offset_index and line_records:
            recs = records_for_span(offset_index, cs, ce)
            pages = sorted(set(r.page for r in recs))
            bbox = compute_bbox_from_records(recs)
        elif page_offsets:
            pages = _page_numbers_for_offsets(cs, ce, page_offsets)
            bbox = _compute_chunk_bbox(chunk_stripped, pages, page_spans or [])

        if headings:
            heading_path = _heading_path_for_position(headings, cs)
            enriched_text = f"[{heading_path}] {chunk_stripped}" if heading_path else chunk_stripped
        else:
            enriched_text = chunk_stripped

        result.append((enriched_text, pages, cs, ce, bbox))

    return result