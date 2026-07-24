"""LLM-based document classification via structured prompts.

Builds a prompt from selected document chunks and category exemplars,
calls the Groq API with a JSON response format, and parses the result
into a structured dictionary.
"""

import json
from groq import Groq

from app.config import settings
from app.constants import CATEGORY_EXEMPLARS, TYPE_FIELDS


def _llm_extract(
    selected_texts: list[str],
    selected_indices: list[int],
    chunk_texts: list[str],
) -> dict:
    """Classify document excerpts by calling the Groq LLM.

    Builds a prompt that asks the LLM to return a JSON object with
    category, confidence, reasoning, title, summary, and per-category
    extraction fields.

    Args:
        selected_texts: Chunk text content selected for classification.
        selected_indices: Corresponding chunk indices (1-indexed in prompt).
        chunk_texts: Full list of all chunk texts (unused directly but
            available for context).

    Returns:
        Parsed JSON dict from the LLM response.
    """
    categories_list = list(CATEGORY_EXEMPLARS.keys())

    fields_prompt_parts = []
    for cat, fields in TYPE_FIELDS.items():
        if not fields:
            continue
        field_list = ", ".join(fields.keys())
        fields_prompt_parts.append(f"- **{cat}**: {field_list}")

    fields_prompt = "\n".join(fields_prompt_parts)

    labeled_chunks = "\n\n".join(
        f"[Chunk {i+1}]: {text}"
        for i, text in enumerate(selected_texts)
    )

    prompt = (
        "You are a procurement document analyst. Analyze the document excerpts below "
        "and return a JSON object with the following fields:\n\n"
        "1. `category`: exactly one of: " + ", ".join(categories_list) + "\n"
        "2. `confidence`: float 0-1\n"
        "3. `reasoning`: brief explanation of why this category was chosen\n"
        "4. `title`: short document title extracted from the text (or null if not found)\n"
        "5. `summary`: 2-3 sentence gist of the document (or null)\n"
        "6. `fields`: an object. Determine the category first, then populate `fields` "
        "using ONLY the field list matching that category. Ignore field lists for other categories.\n\n"
        "Available fields per category:\n"
        f"{fields_prompt}\n\n"
        "For each field, report:\n"
        '  "field_name": {"value": <string or null>, "source_chunk": <integer or null>}\n\n'
        "Rules:\n"
        "- `source_chunk` is the [Chunk N] label number (1-indexed) where the value was found, or null if the field is null.\n"
        "- EVERY field key must always be present. If not found, use value=null and source_chunk=null.\n"
        "- Never omit a key. Never use 'N/A' or empty string. Use null.\n\n"
        "Document excerpts (opening sections and representative content):\n"
        f"{labeled_chunks}\n\n"
        "Instructions:\n"
        "- The category must be exactly one of the listed categories.\n"
        "- If unclear, choose 'Other'.\n"
        "- In reasoning, mention specific signals (e.g., title says RFP, clauses imply contract).\n"
    )

    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=settings.groq_model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
    except Groq.AuthenticationError as e:
        raise ValueError(
            "Invalid GROQ_API_KEY. Check that your key is correct in the .env file."
        ) from e
    content = response.choices[0].message.content
    return json.loads(content)