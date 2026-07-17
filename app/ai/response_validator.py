"""Response Validation.

Every AI provider response must be validated before it reaches business
logic.  This module provides helpers to parse and validate raw provider
text into structured domain models.

Never expose raw provider responses (dicts, JSON strings) outside the
AI layer.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from app.exceptions import InvalidResponseError


def parse_json_response(
    content: str,
    response_model: type[BaseModel] | None = None,
) -> tuple[str, BaseModel | None]:
    """Parse and validate a raw provider response.

    Tries multiple strategies in order of reliability:

        1. Direct JSON parse (fast path for well-behaved models).
        2. Extract JSON from Markdown code fences (`` ```json ... ``` ``).
        3. Extract the first JSON object ``{...}`` by brace matching.

    Args:
        content: Raw text returned by the provider.
        response_model: Optional Pydantic model to validate against.

    Returns:
        A tuple of ``(raw_content, parsed_model)``.

    Raises:
        InvalidResponseError: If the content is not valid JSON or does
            not match the response model.
    """
    raw = content.strip()
    json_str = _extract_json(raw)
    if json_str is None:
        raise InvalidResponseError(
            "Provider response is not valid JSON",
            detail={
                "raw_preview": raw[:500],
                "parse_error": "Could not locate a JSON object in the response",
            },
        )

    try:
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise InvalidResponseError(
            "Provider response is not valid JSON",
            detail={
                "raw_preview": raw[:500],
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
                    "raw_preview": raw[:500],
                },
            ) from exc

    return raw, parsed


def _extract_json(text: str) -> str | None:
    """Attempt to extract a JSON payload from *text*.

    Strategies tried in order:
        1. Direct parse — the whole string is valid JSON.
        2. Strip outer `` ``` `` / `` ```json `` fences then parse.
        3. Find a `` ```json `` block anywhere in the text.
        4. Find the outermost ``{`` … ``}`` pair by brace matching.
    """
    # Strategy 1 — already valid JSON
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # Strategy 2 — whole text is wrapped in code fences
    no_fences = _strip_code_fences(text)
    if no_fences != text:
        try:
            json.loads(no_fences)
            return no_fences
        except json.JSONDecodeError:
            pass

    # Strategy 3 — find a ```json ... ``` block anywhere in the text
    fence_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL
    )
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Strategy 4 — find the first { and match its closing }
    brace_start = text.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[brace_start : i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        # Found braces but invalid JSON — keep looking
                        pass
            if depth < 0:
                break  # malformed; stop

    return None


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
