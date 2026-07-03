"""Response Validation.

Every AI provider response must be validated before it reaches business
logic.  This module provides helpers to parse and validate raw provider
text into structured domain models.

Never expose raw provider responses (dicts, JSON strings) outside the
AI layer.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError

from app.exceptions import InvalidResponseError


def parse_json_response(
    content: str,
    response_model: type[BaseModel] | None = None,
) -> tuple[str, BaseModel | None]:
    """Parse and validate a raw provider response.

    Steps:
        1. Strip code fences (```json ... ```) if present.
        2. Parse as JSON.
        3. If a ``response_model`` is given, validate the parsed JSON
           against it.

    Args:
        content: Raw text returned by the provider.
        response_model: Optional Pydantic model to validate against.

    Returns:
        A tuple of ``(raw_content, parsed_model)``.

    Raises:
        InvalidResponseError: If the content is not valid JSON or does
            not match the response model.
    """
    cleaned = _strip_code_fences(content.strip())

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise InvalidResponseError(
            "Provider response is not valid JSON",
            detail={
                "raw_preview": content[:500],
                "parse_error": str(exc),
            },
        ) from exc

    parsed = None
    if response_model is not None:
        try:
            parsed = response_model.model_validate(data)
        except ValidationError as exc:
            raise InvalidResponseError(
                "Provider response does not match the expected schema",
                detail={
                    "schema": response_model.__name__,
                    "validation_errors": exc.errors(),
                    "raw_preview": content[:500],
                },
            ) from exc

    return content, parsed


def _strip_code_fences(text: str) -> str:
    """Remove Markdown code fences from the beginning/end of text.

    Handles both `` ```json `` and `` ``` `` style fences.
    """
    lines = text.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
