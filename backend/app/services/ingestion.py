"""Document ingestion pipeline.

Orchestrates the full ingestion flow: PDF text extraction, chunking,
embedding generation, NER entity extraction, classification, and
persisting the results to the database.
"""

from sqlalchemy.orm import Session

from app.db.models import Document, Chunk
from app.services.pdf_extraction import extract_text_with_spans
from app.services.chunking import chunk_text
from app.services.embeddings import encode
from app.services.classification import classify
from app.services.ner import extract_chunk_entities


def ingest_document(db: Session, filename: str, pdf_bytes: bytes, content_hash: str) -> Document:
    """Ingest a PDF document: extract, chunk, embed, classify, and persist.

    Args:
        db: SQLAlchemy session.
        filename: Original uploaded filename.
        pdf_bytes: Raw PDF file content.
        content_hash: SHA-256 digest for deduplication.

    Returns:
        The persisted Document with chunks and classification.

    Raises:
        ValueError: If the PDF contains no extractable text.
    """
    extraction = extract_text_with_spans(pdf_bytes)
    raw_text = extraction["full_text"]
    if not raw_text.strip():
        raise ValueError("PDF contains no extractable text")
    page_texts = extraction["page_texts"]
    raw_page_texts = extraction["raw_page_texts"]
    page_spans = extraction["page_spans"]

    chunk_results = chunk_text(
        raw_text,
        page_texts=page_texts,
        raw_page_texts=raw_page_texts,
        page_spans=page_spans,
        line_records=extraction.get("line_records"),
        offset_index=extraction.get("offset_index"),
    )
    chunk_texts = [c[0] for c in chunk_results]
    chunk_page_numbers = [c[1] for c in chunk_results]
    chunk_char_starts = [c[2] for c in chunk_results]
    chunk_char_ends = [c[3] for c in chunk_results]
    chunk_bboxes = [c[4] for c in chunk_results]

    chunk_embeddings = encode(chunk_texts)

    chunk_entities = extract_chunk_entities(chunk_texts)

    classification = classify(
        chunk_embeddings,
        chunk_texts,
        chunk_page_numbers=chunk_page_numbers,
        chunk_bboxes=chunk_bboxes,
    )

    doc = Document(
        filename=filename,
        status="ready",
        category=classification["category"],
        confidence=classification["confidence"],
        reasoning=classification["reasoning"],
        content_hash=content_hash,
        file_data=pdf_bytes,
        page_texts=page_texts,
        chunk_count=len(chunk_texts),
        title=classification.get("title"),
        summary=classification.get("summary"),
        extractions=classification.get("fields"),
    )
    db.add(doc)
    db.flush()

    for i, (ct, emb, entities, pages, cs, ce, bbox) in enumerate(
        zip(chunk_texts, chunk_embeddings, chunk_entities, chunk_page_numbers,
            chunk_char_starts, chunk_char_ends, chunk_bboxes)
    ):
        db.add(Chunk(
            document_id=doc.id,
            chunk_index=i,
            text=ct,
            embedding=emb,
            entities=entities,
            page_numbers=pages,
            char_start=cs,
            char_end=ce,
            bbox=bbox,
        ))

    db.flush()

    extractions = doc.extractions or {}
    if extractions:
        valid_indices = [
            v.get("chunk_index")
            for v in extractions.values()
            if v.get("chunk_index") is not None
        ]
        if valid_indices:
            chunk_index_to_id = {
                ch.chunk_index: ch.id
                for ch in db.query(Chunk).filter(
                    Chunk.document_id == doc.id,
                    Chunk.chunk_index.in_(valid_indices),
                ).all()
            }
            resolved = {}
            for field_name, field_data in extractions.items():
                resolved[field_name] = dict(field_data)
                idx = field_data.get("chunk_index")
                if idx is not None and idx in chunk_index_to_id:
                    resolved[field_name]["chunk_id"] = chunk_index_to_id[idx]
                else:
                    resolved[field_name]["chunk_id"] = None
            doc.extractions = resolved

    return doc