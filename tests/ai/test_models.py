"""Tests for AI domain models."""

from pydantic import BaseModel

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage


class MockResponseModel(BaseModel):
    """Example model for AI response parsing tests."""
    result: str
    score: float = 0.0


def test_ai_request_defaults() -> None:
    """AIRequest sets sensible defaults for optional fields."""
    request = AIRequest(
        system_prompt="You are a helpful assistant.",
        user_message="Analyze this.",
    )
    assert request.system_prompt == "You are a helpful assistant."
    assert request.user_message == "Analyze this."
    assert request.response_model is None
    assert request.model is None
    assert request.temperature is None
    assert request.max_tokens is None


def test_ai_request_with_response_model() -> None:
    """AIRequest stores the response model class (not instance)."""
    request = AIRequest(
        system_prompt="Test",
        user_message="Data",
        response_model=MockResponseModel,
    )
    assert request.response_model is MockResponseModel


def test_ai_response_defaults() -> None:
    """AIResponse has sensible defaults for usage."""
    response = AIResponse(
        content="Hello world",
        provider=ProviderMetadata(
            provider_name="test",
            model="test-model",
            latency_ms=10,
        ),
    )
    assert response.content == "Hello world"
    assert response.parsed is None
    assert response.usage.prompt_tokens == 0
    assert response.usage.completion_tokens == 0
    assert response.usage.total_tokens == 0
    assert response.provider.provider_name == "test"
    assert response.provider.latency_ms == 10


def test_ai_response_with_parsed_model() -> None:
    """AIResponse can carry a parsed Pydantic model."""
    parsed = MockResponseModel(result="ok", score=0.95)
    response = AIResponse(
        content='{"result": "ok", "score": 0.95}',
        parsed=parsed,
        usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        provider=ProviderMetadata(
            provider_name="mock",
            model="mock-model",
            latency_ms=5,
        ),
    )
    assert response.parsed is not None
    assert response.parsed.result == "ok"  # type: ignore[union-attr]
    assert response.usage.total_tokens == 30


def test_token_usage_aggregation() -> None:
    """TokenUsage computes display-friendly values."""
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    assert usage.prompt_tokens + usage.completion_tokens == usage.total_tokens
