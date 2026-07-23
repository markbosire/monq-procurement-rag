"""PDF text extraction with bounding-box spans and line records.

Uses PyMuPDF (fitz) to extract text from each page at the line level,
reorders multi-column layouts, strips headers/boilerplate/page numbers,
and produces clean full-text with per-page span data for rendering and
chunking.
"""

import re
import bisect
from collections import Counter
from dataclasses import dataclass
import fitz
from typing import List, Tuple


@dataclass
class LineRecord:
    """A single line of text with positional metadata from a PDF page."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    is_header: bool = False


def _normalize_whitespace(text: str) -> str:
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _strip_page_numbers(text: str) -> str:
    text = re.sub(r'(?im)^\s*page\s+\d+(\s+of\s+\d+)?\s*$', '', text)
    text = re.sub(r'(?im)^\s*\d+\s+of\s+\d+\s*$', '', text)
    return text


def _strip_blank_page_markers(text: str) -> str:
    return re.sub(r'(?im)^.*this page intentionally left blank.*$', '', text)


def _strip_boilerplate(text: str) -> str:
    text = re.sub(r'(?im)^\s*example\s*$', '', text)
    text = re.sub(r'(?im)^\s*copyright\s+©?\s+\d{4}.*$', '', text)
    return text


def _strip_repeated_headers(text: str) -> str:
    pages = text.split('\n\n')
    if len(pages) < 4:
        return text
    all_lines: list[str] = []
    for page in pages:
        seen = set()
        for line in page.split('\n'):
            stripped = line.strip()
            if len(stripped) > 8:
                seen.add(stripped)
        all_lines.extend(seen)
    line_counts = Counter(all_lines)
    threshold = len(pages) * 0.6
    repeated = {line for line, count in line_counts.items() if count >= threshold}
    if not repeated:
        return text
    result_pages = []
    for page in pages:
        clean_lines = [line for line in page.split('\n') if line.strip() not in repeated]
        result_pages.append('\n'.join(clean_lines))
    return '\n\n'.join(result_pages)


def _collect_bbox_spans(page) -> List[Tuple[float, float, float, float, str]]:
    """Extract (x0, y0, x1, y1, text) spans from a page, one per text line."""
    spans: list[tuple[float, float, float, float, str]] = []
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            bbox = line["bbox"]
            text_parts = []
            for span in line.get("spans", []):
                txt = span.get("text", "").strip()
                if txt:
                    text_parts.append(txt)
            if text_parts:
                spans.append((
                    round(bbox[0], 1),
                    round(bbox[1], 1),
                    round(bbox[2], 1),
                    round(bbox[3], 1),
                    " ".join(text_parts),
                ))
    return spans


def _reorder_columns_bbox(bbox_spans: List[Tuple[float, float, float, float, str]],
                          col_gap: float = 70.0) -> tuple[str, list[dict]]:
    """Reorder bbox spans by column, returning (page_text, span_data_with_offsets).

    Each returned span dict: {x0, y0, x1, y1, text, char_start, char_end}
    where char_start/char_end are offsets into the returned page_text.
    """
    if not bbox_spans:
        return "", []

    ordering_spans = [(s[1], s[0], s[4]) for s in bbox_spans]
    ordering_spans.sort(key=lambda s: (s[0], s[1]))

    x_vals = sorted(set(s[1] for s in ordering_spans))
    clusters: List[List[float]] = []
    for x in x_vals:
        if not clusters:
            clusters.append([x])
        elif x - clusters[-1][-1] > col_gap:
            clusters.append([x])
        else:
            clusters[-1].append(x)

    col_centers = [sum(c) / len(c) for c in clusters]

    def _col_for_x(x0):
        return min(range(len(col_centers)), key=lambda i: abs(col_centers[i] - x0))

    col_entries: List[List[tuple[float, Tuple[float, float, float, float, float, str]]]] = [[] for _ in col_centers]
    for bbox_span in bbox_spans:
        x0, y0, x1, y1, txt = bbox_span
        ci = _col_for_x(x0)
        col_entries[ci].append((y0, bbox_span))

    for c in col_entries:
        c.sort(key=lambda x: x[0])

    page_lines: list[str] = []
    annotated: list[dict] = []
    char_offset = 0
    for col in col_entries:
        for _, (x0, y0, x1, y1, txt) in col:
            line = txt
            page_lines.append(line)
            annotated.append({
                "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "text": txt,
                "char_start": char_offset,
                "char_end": char_offset + len(line),
            })
            char_offset += len(line) + 1

    return "\n".join(page_lines), annotated


def _normalize_record_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'[ \t]+', ' ', text)
    return text


def _is_blank_page_marker(rec: LineRecord) -> bool:
    return bool(re.match(r'(?im)^.*this page intentionally left blank.*$', rec.text))


def _is_page_number(rec: LineRecord) -> bool:
    return bool(
        re.match(r'(?im)^\s*page\s+\d+(\s+of\s+\d+)?\s*$', rec.text)
        or re.match(r'(?im)^\s*\d+\s+of\s+\d+\s*$', rec.text)
    )


def _is_boilerplate_line(rec: LineRecord) -> bool:
    return bool(
        re.match(r'(?im)^\s*example\s*$', rec.text)
        or re.match(r'(?im)^\s*copyright\s+©?\s+\d{4}.*$', rec.text)
    )


def _mark_repeated_headers(records: list[LineRecord], page_heights: dict[int, float] | None = None) -> None:
    """Mark records as headers if they appear near top/bottom on >=60% of pages.

    Modifies records in-place, setting is_header=True on matching records.
    A record must satisfy BOTH conditions to be marked:
    (a) its text appears on >=60% of pages (existing text-repetition check)
    (b) its vertical position is in the top or bottom ~10% of its page

    Args:
        records: Flat list of LineRecord to mutate.
        page_heights: Dict mapping page number -> page height in PDF points.
            If None, computed from records' max y1 per page.
    """
    if not records or len(records) < 4:
        return
    num_pages = max(r.page for r in records)
    if num_pages < 4:
        return

    if page_heights is None:
        page_heights = {}
        page_records: dict[int, list[LineRecord]] = {}
        for rec in records:
            page_records.setdefault(rec.page, []).append(rec)
        for p, recs in page_records.items():
            page_heights[p] = max(r.y1 for r in recs)

    line_page_count: dict[str, set[int]] = {}
    for rec in records:
        stripped = rec.text.strip()
        if len(stripped) > 8:
            line_page_count.setdefault(stripped, set()).add(rec.page)

    threshold = num_pages * 0.6
    repeated_texts = {text for text, pages in line_page_count.items() if len(pages) >= threshold}

    if not repeated_texts:
        return

    for rec in records:
        stripped = rec.text.strip()
        if stripped not in repeated_texts:
            continue
        ph = page_heights.get(rec.page, 792.0)
        top_threshold = 0.1 * ph
        bottom_threshold = 0.9 * ph
        if rec.y0 < top_threshold or rec.y1 > bottom_threshold:
            rec.is_header = True


def _build_line_records(page_spans_list: list[list[dict]]) -> list[LineRecord]:
    records: list[LineRecord] = []
    for page_idx, spans in enumerate(page_spans_list):
        page_num = page_idx + 1
        for sp in spans:
            text = _normalize_record_text(sp.get("text", ""))
            if not text:
                continue
            records.append(LineRecord(
                page=page_num,
                x0=sp["x0"], y0=sp["y0"], x1=sp["x1"], y1=sp["y1"],
                text=text,
            ))
    return records


def _build_full_text_and_index(records: list[LineRecord]) -> tuple[str, list[tuple[int, int, LineRecord]]]:
    if not records:
        return "", []

    lines: list[str] = []
    prev_page = None
    for rec in records:
        if prev_page is not None and rec.page != prev_page:
            lines.append("")
        lines.append(rec.text)
        prev_page = rec.page

    full_text = "\n".join(lines)

    indexed: list[tuple[int, int, LineRecord]] = []
    pos = 0
    rec_idx = 0
    for line in lines:
        if not line:
            pos += 1
            continue
        rec = records[rec_idx]
        indexed.append((pos, pos + len(line), rec))
        pos += len(line) + 1
        rec_idx += 1

    return full_text, indexed


def _build_page_texts(records: list[LineRecord], total_pages: int) -> list[str]:
    page_lines: dict[int, list[str]] = {}
    for rec in records:
        page_lines.setdefault(rec.page, []).append(rec.text)
    result: list[str] = []
    for i in range(1, total_pages + 1):
        lines = page_lines.get(i, [])
        if lines:
            result.append("\n".join(lines))
        else:
            result.append("")
    return result


def records_for_span(indexed: list[tuple[int, int, LineRecord]], cs: int, ce: int) -> list[LineRecord]:
    """Return the LineRecords overlapping the character range [cs, ce).

    Uses binary search for efficient lookup over a pre-built index.

    Args:
        indexed: List of (start, end, LineRecord) tuples sorted by start.
        cs: Start character position.
        ce: End character position.

    Returns:
        List of LineRecord overlapping the requested span.
    """
    if not indexed:
        return []
    starts = [s for s, _, _ in indexed]
    end_pos = bisect.bisect_left(starts, ce)
    result: list[LineRecord] = []
    for i in range(end_pos):
        s, e, rec = indexed[i]
        if e > cs:
            result.append(rec)
    return result


def compute_bbox_from_records(records: list[LineRecord]) -> list[dict]:
    """Convert a list of LineRecord into bounding box dicts, excluding headers.

    Args:
        records: LineRecord objects.

    Returns:
        List of bbox dicts with keys: page, x0, y0, x1, y1.
    """
    return [
        {"page": r.page, "x0": r.x0, "y0": r.y0, "x1": r.x1, "y1": r.y1}
        for r in records if not r.is_header
    ]


def extract_text(pdf_bytes: bytes) -> tuple[str, list[str]]:
    """Extract cleaned full text and per-page texts from a PDF.

    Convenience wrapper around extract_text_with_spans.

    Args:
        pdf_bytes: Raw PDF file content.

    Returns:
        Tuple of (full_text, page_texts).
    """
    data = extract_text_with_spans(pdf_bytes)
    return data["full_text"], data["page_texts"]


def extract_text_with_spans(pdf_bytes: bytes) -> dict:
    """Extract text with full bbox span data for PDF rendering.

    Args:
        pdf_bytes: Raw PDF file content.

    Returns:
        Dict with keys:
            full_text: Cleaned full document text (headers excluded).
            page_texts: Cleaned per-page texts (headers excluded).
            raw_page_texts: Raw (pre-cleaning) per-page texts.
            page_spans: Per-page list of span dicts {x0, y0, x1, y1, text, char_start, char_end}.
            line_records: Flat list of ALL LineRecord after cleaning, with is_header marked.
            offset_index: List of (start, end, LineRecord) for non-header records.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    raw_page_texts: list[str] = []
    all_page_spans: list[list[dict]] = []
    page_heights: dict[int, float] = {}

    for idx, page in enumerate(doc):
        page_heights[idx + 1] = page.rect.height
        bbox_spans = _collect_bbox_spans(page)
        page_text, annotated = _reorder_columns_bbox(bbox_spans)
        raw_page_texts.append(page_text)
        all_page_spans.append(annotated)
    doc.close()

    records = _build_line_records(all_page_spans)
    records = [r for r in records if not _is_blank_page_marker(r)]
    records = [r for r in records if not _is_page_number(r)]
    records = [r for r in records if not _is_boilerplate_line(r)]
    _mark_repeated_headers(records, page_heights)

    content_records = [r for r in records if not r.is_header]
    full_text, offset_index = _build_full_text_and_index(content_records)
    page_texts = _build_page_texts(content_records, total_pages)

    return {
        "full_text": full_text,
        "page_texts": page_texts,
        "raw_page_texts": raw_page_texts,
        "page_spans": all_page_spans,
        "line_records": records,
        "offset_index": offset_index,
    }