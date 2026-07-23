import pytest
from app.services.chunking import _detect_headings, chunk_text
from app.services.retrieval import BM25, _minmax_norm


# ─── Heading Detection Tests ─────────────────────────────────────────────────

class TestDetectHeadings:
    def test_empty_text(self):
        assert _detect_headings("") == []

    def test_simple_heading(self):
        text = "GENERAL\n\nSome content here."
        headings = _detect_headings(text)
        assert len(headings) >= 1
        assert headings[0][1] == "GENERAL"

    def test_section_heading(self):
        text = "SECTION 1. INSTRUCTIONS\n\nBody text."
        headings = _detect_headings(text)
        assert any("SECTION 1" in h[1] for h in headings)

    def test_lettered_heading(self):
        text = "A. GENERAL PROVISIONS\n\nBody text."
        headings = _detect_headings(text)
        assert any("A. GENERAL PROVISIONS" in h[1] for h in headings)

    def test_numbered_heading(self):
        text = "1. Definitions\n\nBody text."
        headings = _detect_headings(text)
        assert any("1. Definitions" in h[1] for h in headings)

    def test_no_false_positive_address(self):
        text = "P. O. Box 100746\nNAIROBI\n"
        headings = _detect_headings(text)
        for _, h, _ in headings:
            assert "P. O. Box" not in h

    def test_no_false_positive_boilerplate(self):
        text = "Tel: +254 719 037000\nEmail: test@example.com\n"
        headings = _detect_headings(text)
        assert len(headings) == 0

    def test_multi_level_headings(self):
        text = (
            "SECTION 1. TERMS\n\n"
            "A. Delivery Terms\n\n"
            "1. Timeline\n\n"
            "Delivery shall be within 30 days.\n\n"
            "2. Location\n\n"
            "Delivery shall be to Nairobi.\n\n"
        )
        headings = _detect_headings(text)
        levels = [h[2] for h in headings]
        assert 1 in levels  # SECTION
        assert 2 in levels  # A.
        assert 3 in levels  # 1., 2.

    def test_skips_table_of_contents(self):
        text = "GENERAL ...................... 3\nSECTION 1 .................... 4\n"
        headings = _detect_headings(text)
        for _, h, _ in headings:
            assert "......................" not in h


# ─── Heading Context Enrichment Tests ────────────────────────────────────────

class TestChunkWithHeadings:
    def test_short_text_no_headings(self):
        text = "Short document with no headings."
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        chunk_strings = [c[0] for c in chunks]
        assert all(not c.startswith("[") for c in chunk_strings)

    def test_heading_prepended_to_chunks(self):
        text = "SECTION 1. PRICING\n\nThe total cost is $1,500."
        chunks = chunk_text(text)
        chunk_strings = [c[0] for c in chunks]
        has_heading = any("SECTION 1" in c for c in chunk_strings)
        assert has_heading

    def test_chunk_within_section_gets_heading_context(self):
        long_text = (
            "SECTION 1. TERMS\n\n"
            "A. Delivery\n\n"
            "Delivery shall be completed within 30 calendar days "
            "from the date of the order. The vendor shall bear all "
            "shipping costs. Late delivery may incur penalties as "
            "per the agreed schedule.\n\n"
            "B. Payment\n\n"
            "Payment shall be made within 60 days of invoice. "
        )
        text = long_text + "All amounts are in USD. " * 40
        chunks = chunk_text(text)
        chunk_strings = [c[0] for c in chunks]
        delivery_chunks = [c for c in chunk_strings if "30 calendar days" in c]
        payment_chunks = [c for c in chunk_strings if "60 days" in c]

        assert len(delivery_chunks) >= 1
        assert len(payment_chunks) >= 1
        delivery_enriched = delivery_chunks[0]
        payment_enriched = payment_chunks[0]

        assert "SECTION 1. TERMS" in delivery_enriched
        assert "Delivery" in delivery_enriched or "A." in delivery_enriched
        assert "30 calendar days" in delivery_enriched

        assert payment_enriched != delivery_enriched
        assert "60 days" in payment_enriched


# ─── BM25 Tests ──────────────────────────────────────────────────────────────

class TestBM25:
    def test_empty_corpus(self):
        bm25 = BM25([])
        assert bm25.get_scores("test") == []

    def test_single_document(self):
        bm25 = BM25(["the cat sat on the mat"])
        scores = bm25.get_scores("cat mat")
        assert scores[0] > 0

    def test_relevant_document_scores_higher(self):
        corpus = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a programming language for software development",
            "The cat sat on the mat and looked at the dog",
        ]
        bm25 = BM25(corpus)
        scores = bm25.get_scores("dog fox")
        assert scores[0] > scores[1]
        assert scores[2] > scores[1]


# ─── Normalization Tests ─────────────────────────────────────────────────────

class TestMinMaxNorm:
    def test_all_same_values(self):
        assert _minmax_norm([5.0, 5.0, 5.0]) == [0.5, 0.5, 0.5]

    def test_single_value(self):
        assert _minmax_norm([42.0]) == [0.5]

    def test_typical_values(self):
        result = _minmax_norm([0.0, 0.5, 1.0])
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(1.0)

    def test_empty_list(self):
        assert _minmax_norm([]) == []


# ─── Integration: structured document retrieval ──────────────────────────────

def test_heading_chunking_on_long_structured_text():
    text = (
        "SECTION 1. GENERAL PROVISIONS\n\n"
        "1. Definitions\n\n"
        "In this Agreement, unless the context otherwise requires:\n"
        "(a) 'Affiliate' means any entity that controls, is controlled by or "
        "is under common control with a party;\n"
        "(b) 'Agreement' means this agreement and all schedules attached;\n"
        "(c) 'Business Day' means a day other than a Saturday, Sunday or "
        "public holiday in Kenya.\n\n"
        "2. Interpretation\n\n"
        "In this Agreement, words importing the singular shall include the "
        "plural and vice versa. Headings are for convenience only and shall "
        "not affect the interpretation of this Agreement.\n\n"
        "3. Entire Agreement\n\n"
        "This Agreement constitutes the entire agreement between the parties "
        "with respect to the subject matter hereof and supersedes all prior "
        "negotiations, representations or agreements.\n\n"
        "SECTION 2. FINANCIAL TERMS\n\n"
        "1. Payment\n\n"
        "The Customer shall pay the Provider the fees set out in the "
        "Statement of Work. All fees are exclusive of taxes. Payment shall "
        "be made within 30 days of receipt of a valid invoice.\n\n"
        "2. Reference Number\n\n"
        "The reference number for this RFP is GDC/DU/RFP/067/2022:2023. All "
        "correspondence must quote this reference number.\n\n"
        "3. Late Payment\n\n"
        "If the Customer fails to pay any amount when due, the Provider "
        "may charge interest at 1.5% per month on the outstanding amount.\n\n"
        "SECTION 3. DELIVERY TERMS\n\n"
        "1. Delivery Schedule\n\n"
        "All goods shall be delivered within 30 days of the effective date. "
        "The Provider shall bear all risk of loss until delivery is completed "
        "and accepted in writing by the Customer. Partial deliveries are "
        "permitted only with prior written consent.\n\n"
        "2. Inspection\n\n"
        "The Customer shall have 10 business days from delivery to inspect "
        "the goods and notify the Provider of any defects or non-conformities. "
        "If no such notice is given, the goods shall be deemed accepted.\n\n"
        "3. Force Majeure\n\n"
        "Neither party shall be liable for any failure or delay in "
        "performance caused by events beyond its reasonable control including "
        "but not limited to acts of God, war, strikes, or government "
        "regulations. The affected party shall notify the other promptly.\n\n"
    )
    chunks = chunk_text(text)
    chunk_strings = [c[0] for c in chunks]

    assert len(chunks) >= 3
    for c in chunk_strings:
        assert c.startswith("["), f"Chunk missing heading: {c[:50]}"

    ref_chunks = [c for c in chunk_strings if "GDC/DU/RFP/067/2022:2023" in c]
    assert len(ref_chunks) >= 1
    ref_text = ref_chunks[0]
    assert "SECTION 2. FINANCIAL TERMS" in ref_text
    assert "Reference Number" in ref_text or "reference number" in ref_text


import pytest
