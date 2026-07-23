"""Tests for PDF text extraction service.

Uses synthetic PDFs generated with fpdf2 to verify extraction logic
including multi-page, multi-column, header detection, and utility functions.
"""

from fpdf import FPDF
import pytest

from app.services.pdf_extraction import (
    extract_text_with_spans,
    extract_text,
    LineRecord,
    _is_blank_page_marker,
    _is_page_number,
    _is_boilerplate_line,
    _normalize_record_text,
    _normalize_whitespace,
    _strip_page_numbers,
    _strip_blank_page_markers,
    _strip_boilerplate,
    _mark_repeated_headers,
    records_for_span,
    compute_bbox_from_records,
    _reorder_columns_bbox,
    _collect_bbox_spans,
)


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def _make_simple_pdf(text: str = "Hello World. This is a test document.") -> bytes:
    """Create a single-page PDF with the given text."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, text)
    raw = pdf.output()
    return raw if isinstance(raw, bytes) else bytes(raw)


def _make_multi_page_pdf(num_pages: int = 3) -> bytes:
    """Create a multi-page PDF with unique text on each page."""
    pdf = FPDF()
    for i in range(1, num_pages + 1):
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, f"This is page {i} of the document.")
    raw = pdf.output()
    return raw if isinstance(raw, bytes) else bytes(raw)


def _make_multi_column_pdf() -> bytes:
    """Create a PDF with two columns of text using absolute x positioning."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.set_xy(10, 10)
    pdf.multi_cell(80, 10, "Left column text line A.")
    pdf.set_xy(10, pdf.get_y())
    pdf.multi_cell(80, 10, "Left column text line B.")
    pdf.set_xy(110, 10)
    pdf.multi_cell(80, 10, "Right column text line C.")
    pdf.set_xy(110, pdf.get_y())
    pdf.multi_cell(80, 10, "Right column text line D.")
    raw = pdf.output()
    return raw if isinstance(raw, bytes) else bytes(raw)


def _make_pdf_with_repeated_headers() -> bytes:
    """Create a 4-page PDF where each page has a repeated header line."""
    pdf = FPDF()
    for i in range(1, 5):
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, "Confidential Header", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"Content unique to page {i}.", new_x="LMARGIN", new_y="NEXT")
    raw = pdf.output()
    return raw if isinstance(raw, bytes) else bytes(raw)


# ---------------------------------------------------------------------------
# Basic extraction tests
# ---------------------------------------------------------------------------

def test_extract_text_with_spans_single_page():
    """Verify extract_text_with_spans returns expected dict structure for a single-page PDF."""
    raw = _make_simple_pdf()
    result = extract_text_with_spans(raw)
    assert isinstance(result, dict)
    assert "full_text" in result
    assert "page_texts" in result
    assert "page_spans" in result
    assert "line_records" in result
    assert "offset_index" in result


def test_extract_text_with_spans_content():
    """Verify the extracted full_text contains the text written to the PDF."""
    raw = _make_simple_pdf("Hello World. This is a test document.")
    result = extract_text_with_spans(raw)
    assert "Hello World" in result["full_text"]
    assert "test document" in result["full_text"]


def test_extract_text_returns_text_and_page_texts():
    """Verify extract_text returns (full_text, page_texts) tuple."""
    raw = _make_simple_pdf()
    full_text, page_texts = extract_text(raw)
    assert isinstance(full_text, str)
    assert isinstance(page_texts, list)
    assert len(page_texts) >= 1


# ---------------------------------------------------------------------------
# Multi-page tests
# ---------------------------------------------------------------------------

def test_multi_page_extraction():
    """Create a 3-page PDF and verify page_texts has 3 entries and full_text contains text from all pages."""
    raw = _make_multi_page_pdf(3)
    result = extract_text_with_spans(raw)
    assert len(result["page_texts"]) == 3
    assert "page 1" in result["full_text"]
    assert "page 2" in result["full_text"]
    assert "page 3" in result["full_text"]


# ---------------------------------------------------------------------------
# Column reordering tests
# ---------------------------------------------------------------------------

def test_reorder_columns_bbox():
    """Create a page with two columns of text and test _reorder_columns_bbox with manually constructed bbox_spans."""
    bbox_spans = [
        (10.0, 10.0, 90.0, 20.0, "Left A"),
        (10.0, 25.0, 90.0, 35.0, "Left B"),
        (110.0, 10.0, 190.0, 20.0, "Right A"),
        (110.0, 25.0, 190.0, 35.0, "Right B"),
    ]
    page_text, annotated = _reorder_columns_bbox(bbox_spans, col_gap=50.0)
    assert "Left A" in page_text
    assert "Left B" in page_text
    assert "Right A" in page_text
    assert "Right B" in page_text
    assert len(annotated) == 4


def test_reorder_columns_empty():
    """Empty spans returns empty string and empty list."""
    page_text, annotated = _reorder_columns_bbox([])
    assert page_text == ""
    assert annotated == []


# ---------------------------------------------------------------------------
# Header detection tests
# ---------------------------------------------------------------------------

def test_mark_repeated_headers():
    """Construct LineRecord list with a line appearing on multiple pages within top 10% — it should be marked as header."""
    records = [
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=1, x0=10, y0=100, x1=100, y1=110, text="Body alpha"),
        LineRecord(page=2, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=2, x0=10, y0=100, x1=100, y1=110, text="Body beta"),
        LineRecord(page=3, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=3, x0=10, y0=100, x1=100, y1=110, text="Body gamma"),
        LineRecord(page=4, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=4, x0=10, y0=100, x1=100, y1=110, text="Body delta"),
    ]
    _mark_repeated_headers(records)
    header_recs = [r for r in records if r.is_header]
    assert len(header_recs) == 4
    for r in header_recs:
        assert r.text.strip() == "Header Line"



def test_mark_repeated_headers_below_threshold():
    """Line appears on fewer than 60% of pages — not marked as header."""
    records = [
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=1, x0=10, y0=100, x1=100, y1=110, text="P1 body"),
        LineRecord(page=2, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=2, x0=10, y0=100, x1=100, y1=110, text="P2 body"),
        LineRecord(page=3, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=3, x0=10, y0=100, x1=100, y1=110, text="P3 body"),
        LineRecord(page=4, x0=10, y0=100, x1=100, y1=110, text="P4 body"),
        LineRecord(page=5, x0=10, y0=100, x1=100, y1=110, text="P5 body"),
        LineRecord(page=6, x0=10, y0=100, x1=100, y1=110, text="P6 body"),
    ]
    _mark_repeated_headers(records)
    header_recs = [r for r in records if r.is_header]
    assert len(header_recs) == 0
    _mark_repeated_headers(records)
    header_recs = [r for r in records if r.is_header]
    assert len(header_recs) == 4
    for r in header_recs:
        assert r.text.strip() == "Header Line"


def test_mark_repeated_headers_below_threshold():
    """Line appears on fewer than 60% of pages — not marked as header."""
    records = [
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="Header Line"),
        LineRecord(page=1, x0=10, y0=200, x1=100, y1=210, text="Body"),
        LineRecord(page=2, x0=10, y0=200, x1=100, y1=210, text="Body"),
        LineRecord(page=3, x0=10, y0=200, x1=100, y1=210, text="Body"),
        LineRecord(page=4, x0=10, y0=200, x1=100, y1=210, text="Body"),
    ]
    _mark_repeated_headers(records)
    header_recs = [r for r in records if r.is_header]
    assert len(header_recs) == 0


def test_mark_repeated_headers_few_pages():
    """Fewer than 4 pages — no headers marked."""
    records = [
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="Header"),
        LineRecord(page=2, x0=10, y0=5, x1=100, y1=15, text="Header"),
        LineRecord(page=3, x0=10, y0=5, x1=100, y1=15, text="Header"),
    ]
    _mark_repeated_headers(records)
    assert all(not r.is_header for r in records)


def test_mark_repeated_headers_few_records():
    """Fewer than 4 records — no headers marked."""
    records = [
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="Header"),
        LineRecord(page=2, x0=10, y0=5, x1=100, y1=15, text="Header"),
        LineRecord(page=3, x0=10, y0=5, x1=100, y1=15, text="Header"),
    ]
    _mark_repeated_headers(records)
    assert all(not r.is_header for r in records)


# ---------------------------------------------------------------------------
# LineRecord helpers
# ---------------------------------------------------------------------------

def test_is_blank_page_marker():
    """LineRecord with 'This page intentionally left blank' returns True."""
    rec = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="This page intentionally left blank")
    assert _is_blank_page_marker(rec) is True
    rec2 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="Content page")
    assert _is_blank_page_marker(rec2) is False


def test_is_page_number():
    """'Page 1 of 5' and '1 of 5' return True; 'Content page' returns False."""
    rec1 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="Page 1 of 5")
    assert _is_page_number(rec1) is True
    rec2 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="1 of 5")
    assert _is_page_number(rec2) is True
    rec3 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="Content page")
    assert _is_page_number(rec3) is False


def test_is_boilerplate_line():
    """'EXAMPLE' and 'Copyright © 2024' return True; 'Content' returns False."""
    rec1 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="EXAMPLE")
    assert _is_boilerplate_line(rec1) is True
    rec2 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="Copyright \u00a9 2024")
    assert _is_boilerplate_line(rec2) is True
    rec3 = LineRecord(page=1, x0=0, y0=0, x1=0, y1=0, text="Content")
    assert _is_boilerplate_line(rec3) is False


def test_normalize_record_text():
    """Strips whitespace and collapses multiple spaces."""
    assert _normalize_record_text("  hello   world  ") == "hello world"
    assert _normalize_record_text("foo") == "foo"
    assert _normalize_record_text("  ") == ""


# ---------------------------------------------------------------------------
# records_for_span and compute_bbox_from_records
# ---------------------------------------------------------------------------

def test_records_for_span():
    """With indexed records, verify correct LineRecords returned for a (cs, ce) range."""
    rec_a = LineRecord(page=1, x0=0, y0=0, x1=10, y1=10, text="alpha")
    rec_b = LineRecord(page=1, x0=0, y0=10, x1=10, y1=20, text="beta")
    rec_c = LineRecord(page=1, x0=0, y0=20, x1=10, y1=30, text="gamma")
    indexed = [(0, 5, rec_a), (6, 10, rec_b), (11, 16, rec_c)]
    result = records_for_span(indexed, 0, 10)
    assert rec_a in result
    assert rec_b in result
    assert rec_c not in result


def test_records_for_span_empty():
    """Empty indexed returns empty list."""
    assert records_for_span([], 0, 10) == []


def test_compute_bbox_from_records():
    """Records with is_header=False produce correct bbox dicts; header records are excluded."""
    records = [
        LineRecord(page=1, x0=10, y0=20, x1=100, y1=30, text="body", is_header=False),
        LineRecord(page=1, x0=10, y0=5, x1=100, y1=15, text="head", is_header=True),
    ]
    bboxes = compute_bbox_from_records(records)
    assert len(bboxes) == 1
    assert bboxes[0] == {"page": 1, "x0": 10, "y0": 20, "x1": 100, "y1": 30}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def test_normalize_whitespace():
    """Strips trailing spaces and collapses 3+ newlines to 2."""
    text = "  hello   \n\n\n\nworld  "
    result = _normalize_whitespace(text)
    assert result == "hello\n\nworld"


def test_strip_page_numbers():
    """'Page 1' and 'Page 1 of 5' lines are removed."""
    text = "Page 1\nSome content\nPage 1 of 5\nMore content"
    result = _strip_page_numbers(text)
    assert "Page 1" not in result
    assert "Page 1 of 5" not in result
    assert "Some content" in result
    assert "More content" in result


def test_strip_blank_page_markers():
    """'This page intentionally left blank' line is removed."""
    text = "This page intentionally left blank\nSome content"
    result = _strip_blank_page_markers(text)
    assert "This page intentionally left blank" not in result
    assert "Some content" in result


def test_strip_boilerplate():
    """'Example' and 'Copyright © 2024' lines are removed."""
    text = "Example\nSome content\nCopyright \u00a9 2024"
    result = _strip_boilerplate(text)
    assert "Example" not in result
    assert "Copyright" not in result
    assert "Some content" in result
