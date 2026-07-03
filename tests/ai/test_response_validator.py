"""Tests for response validation."""

import pytest
from pydantic import BaseModel, Field

from app.ai.response_validator import (
    _strip_code_fences,
    parse_json_response,
)
from app.exceptions import InvalidResponseError


class _ResultModel(BaseModel):
    """Simple model for validation tests (prefixed with _ to avoid pytest collection)."""
    result: str
    score: float = Field(default=0.0)


class _NestedModel(BaseModel):
    """Model with nested structure."""
    name: str
    data: dict[str, str]


def test_strip_code_fences_json() -> None:
    """Strip ```json ... ``` fences."""
    text = '```json\n{"key": "value"}\n```'
    assert _strip_code_fences(text) == '{"key": "value"}'


def test_strip_code_fences_no_fences() -> None:
    """Return text unchanged if no fences."""
    text = '{"key": "value"}'
    assert _strip_code_fences(text) == '{"key": "value"}'


def test_strip_code_fences_plain_fences() -> None:
    """Strip plain ``` fences."""
    text = '```\n{"key": "value"}\n```'
    assert _strip_code_fences(text) == '{"key": "value"}'


def test_parse_valid_json() -> None:
    """Valid JSON is parsed correctly."""
    content, parsed = parse_json_response(
        '{"result": "success", "score": 0.95}',
        _ResultModel,
    )
    assert isinstance(parsed, _ResultModel)
    assert parsed.result == "success"
    assert parsed.score == 0.95


def test_parse_valid_json_no_model() -> None:
    """Valid JSON without a response model returns None for parsed."""
    content, parsed = parse_json_response('{"key": "value"}')
    assert parsed is None
    assert '{"key": "value"}' in content


def test_parse_invalid_json() -> None:
    """Invalid JSON raises InvalidResponseError."""
    with pytest.raises(InvalidResponseError, match="not valid JSON"):
        parse_json_response("not json at all")


def test_parse_json_fails_schema_validation() -> None:
    """JSON that doesn't match response model raises InvalidResponseError."""
    with pytest.raises(InvalidResponseError) as exc:
        parse_json_response('{"wrong_field": "value"}', _ResultModel)
    assert "schema" in str(exc.value.detail or {})


def test_parse_json_with_code_fences() -> None:
    """JSON inside code fences is correctly parsed."""
    content, parsed = parse_json_response(
        '```json\n{"result": "ok", "score": 1.0}\n```',
        _ResultModel,
    )
    assert parsed is not None
    assert parsed.result == "ok"


def test_parse_json_nested() -> None:
    """Nested JSON models parse correctly."""
    content, parsed = parse_json_response(
        '{"name": "test", "data": {"key": "value"}}',
        _NestedModel,
    )
    assert parsed is not None
    assert parsed.name == "test"
    assert parsed.data["key"] == "value"
