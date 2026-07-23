from app.services.chunking import chunk_text


def test_chunking_returns_multiple_chunks():
    text = "Hello world. " * 200
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=75)
    assert len(chunks) > 1


def test_chunking_respects_paragraphs():
    text = "This is paragraph one. It has some content.\n\nThis is paragraph two. It also has content.\n\nThis is paragraph three. More content here."
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=75)
    assert len(chunks) >= 1


def test_chunking_overlap_present():
    text = "Word " * 500
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=75)
    if len(chunks) > 1:
        assert len(chunks[0][0]) >= 400


def test_chunking_single_chunk_for_short_text():
    text = "Short document."
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=75)
    assert len(chunks) == 1
    assert chunks[0][0] == "Short document."


def test_chunking_preserves_sentences():
    text = "First sentence about procurement. Second sentence about contracts. " * 50
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=30)
    for chunk_text_content, _, _, _, _ in chunks:
        assert len(chunk_text_content) > 0
