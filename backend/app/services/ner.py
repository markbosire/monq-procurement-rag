"""Named Entity Recognition (NER) extraction from document chunks.

Uses spaCy's en_core_web_sm model to extract named entities from chunk
texts, used for entity-type boosting during retrieval.
"""

from functools import lru_cache
from typing import List


@lru_cache(maxsize=1)
def _load_nlp():
    import spacy
    return spacy.load("en_core_web_sm")


def extract_chunk_entities(chunk_texts: list[str]) -> list[list[dict]]:
    """Extract named entities from each chunk text.

    Truncates each chunk to the first 10,000 characters for performance.

    Args:
        chunk_texts: List of chunk text strings.

    Returns:
        List of entity lists, where each entity is a dict with 'text' and 'label'.
    """
    nlp = _load_nlp()
    all_entities: list[list[dict]] = []
    for text in chunk_texts:
        doc = nlp(text[:10000])
        entities = [
            {"text": ent.text, "label": ent.label_}
            for ent in doc.ents
        ]
        all_entities.append(entities)
    return all_entities


def extract_entity_types(text: str) -> set[str]:
    """Extract unique entity label types from a text snippet.

    Args:
        text: Input text (truncated to 2000 chars).

    Returns:
        Set of entity label strings (e.g. {'ORG', 'DATE', 'MONEY'}).
    """
    nlp = _load_nlp()
    doc = nlp(text[:2000])
    return set(ent.label_ for ent in doc.ents)