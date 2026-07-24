"""RAG (Retrieval-Augmented Generation) question-answering pipeline.

Retrieves relevant chunks from a document, enriches them with boundary
context, builds a prompt with document metadata and chat history, calls
the Groq LLM for an answer, and resolves cited source chunks.
"""

import json
from groq import Groq
from app.config import settings
from app.services.retrieval import retrieve_chunks

BOUNDARY_PAD_CHARS = 150

SOURCE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "sources": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "List of chunk IDs from the document context that support the answer. Empty array if answer not found in context.",
        },
    },
    "required": ["answer", "sources"],
    "additionalProperties": False,
}

def _format_known_fields(doc_extractions: dict | None) -> str:
    if not doc_extractions:
        return ""
    lines = []
    for field_name, field_data in doc_extractions.items():
        if isinstance(field_data, dict):
            val = field_data.get("value")
        else:
            val = field_data
        if val is not None and val != "" and val != "N/A":
            lines.append(f"  {field_name}: {val}")
    if not lines:
        return ""
    return "Known extracted fields for this document (may or may not be relevant to the question):\n" + "\n".join(lines) + "\n\n"


def _pad_with_boundary_context(
    chunk_text: str, prev_text: str | None, next_text: str | None, pad_chars: int = BOUNDARY_PAD_CHARS
) -> str:
    text = chunk_text
    if prev_text:
        tail = prev_text[-pad_chars:]
        if " " in tail:
            tail = tail.split(" ", 1)[-1]
        text = f"...{tail}\n{text}"
    if next_text:
        head = next_text[:pad_chars]
        if " " in head:
            head = head.rsplit(" ", 1)[0]
        text = f"{text}\n{head}..."
    return text


def build_prompt(
    question: str,
    context_chunks: list[str],
    history: list[dict] | None = None,
    doc_category: str | None = None,
    doc_title: str | None = None,
    known_fields: str = "",
) -> list[dict]:
    """Build the message list for the LLM chat completion.

    Constructs a system prompt with document info, known extracted fields,
    and the retrieved context chunks, then appends conversation history
    and the user's question.

    Args:
        question: The user's question.
        context_chunks: Retrieved chunk texts.
        history: Optional list of previous conversation messages.
        doc_category: Document classification category.
        doc_title: Document title.
        known_fields: Formatted string of known extracted fields.

    Returns:
        List of message dicts suitable for the Groq API.
    """
    preamble = ""
    if doc_category or doc_title:
        parts = []
        if doc_title:
            parts.append(f"Title: {doc_title}")
        if doc_category:
            parts.append(f"Category: {doc_category}")
        preamble = "Document info \u2014 " + "; ".join(parts) + ".\n\n"

    system_prompt = (
        "You are a procurement document assistant. Answer the user's question based solely on the "
        "provided document context below. If the answer cannot be found in the context, say so plainly. "
        "Do not use any outside knowledge or make up information.\n\n"
        "You MUST respond in JSON format with two fields:\n"
        "- \"answer\": your response to the question (string)\n"
        "- \"sources\": array of chunk numbers (integers) from the [Chunk N] labels that support your answer. "
        "If no chunk supports the answer, use an empty array.\n\n"
        + preamble
        + known_fields
        + "Document context:\n"
        + "\n\n".join(f"[Chunk {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks))
    )
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def answer_question(
    db_session,
    document_id: int,
    question: str,
    history: list[dict] | None = None,
    doc_category: str | None = None,
    doc_title: str | None = None,
    doc_extractions: dict | None = None,
) -> dict:
    """Answer a question about a document using RAG.

    Retrieves relevant chunks, enriches them with boundary context from
    neighbouring chunks, builds a prompt, calls the LLM, and resolves
    the source chunk references cited in the LLM response.

    Args:
        db_session: SQLAlchemy database session.
        document_id: Document UUID.
        question: The user's question.
        history: Previous conversation messages.
        doc_category: Document category for the prompt.
        doc_title: Document title for the prompt.
        doc_extractions: Known extracted fields for context.

    Returns:
        Dict with keys 'answer' (str) and 'source_chunks' (list of dict).
    """
    context_chunks, source_ids = retrieve_chunks(db_session, document_id, question)
    known_fields = _format_known_fields(doc_extractions)

    from app.db.models import Chunk

    padded_contexts = list(context_chunks)
    if source_ids:
        matched_chunks = (
            db_session.query(Chunk)
            .filter(Chunk.id.in_(source_ids))
            .all()
        )
        id_to_chunk = {c.id: c for c in matched_chunks}
        matched_indices = {c.chunk_index for c in matched_chunks}
        neighbor_indices = set()
        for c in matched_chunks:
            if c.chunk_index > 0:
                neighbor_indices.add(c.chunk_index - 1)
            neighbor_indices.add(c.chunk_index + 1)
        neighbor_indices -= matched_indices
        neighbors = (
            db_session.query(Chunk)
            .filter(Chunk.document_id == document_id, Chunk.chunk_index.in_(neighbor_indices))
            .all()
        ) if neighbor_indices else []
        text_by_index = {c.chunk_index: c.text for c in matched_chunks}
        text_by_index.update({c.chunk_index: c.text for c in neighbors})
        for i, cid in enumerate(source_ids):
            chunk = id_to_chunk.get(cid)
            if not chunk:
                continue
            prev_text = text_by_index.get(chunk.chunk_index - 1)
            next_text = text_by_index.get(chunk.chunk_index + 1)
            padded_contexts[i] = _pad_with_boundary_context(chunk.text, prev_text, next_text)

    messages = build_prompt(question, padded_contexts, history, doc_category, doc_title, known_fields)

    client = Groq(api_key=settings.groq_api_key)
    try:
        response = client.chat.completions.create(
            model=settings.groq_model_name,
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
    except Groq.AuthenticationError as e:
        raise ValueError(
            "Invalid GROQ_API_KEY. Check that your key is correct in the .env file."
        ) from e

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        answer_text = parsed.get("answer", raw)
        cited_positions = parsed.get("sources", [])
    except (json.JSONDecodeError, TypeError):
        answer_text = raw
        cited_positions = []

    all_chunks_data: list[dict] = []
    if source_ids:
        chunk_objs = (
            db_session.query(Chunk)
            .filter(Chunk.id.in_(source_ids))
            .all()
        )
        chunk_map = {c.id: c for c in chunk_objs}
        for cid in source_ids:
            c = chunk_map.get(cid)
            if c:
                all_chunks_data.append({
                    "id": c.id,
                    "text": c.text,
                    "page_numbers": c.page_numbers if c.page_numbers else [],
                    "bbox": c.bbox if c.bbox else [],
                })

    position_to_db_id = {}
    for i, sid in enumerate(source_ids):
        position_to_db_id[i + 1] = sid

    if cited_positions:
        resolved_ids = set()
        for pos in cited_positions:
            actual_id = position_to_db_id.get(pos)
            if actual_id:
                resolved_ids.add(actual_id)
        source_chunks_data = [cd for cd in all_chunks_data if cd["id"] in resolved_ids] or all_chunks_data
    else:
        source_chunks_data = all_chunks_data

    return {
        "answer": answer_text,
        "source_chunks": source_chunks_data,
    }