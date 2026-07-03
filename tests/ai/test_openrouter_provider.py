"""Tests for OpenRouterProvider."""

import json

import httpx
import pytest
from pydantic import BaseModel

from app.ai.models import AIRequest
from app.ai.providers.openrouter import OpenRouterProvider
from app.exceptions import (
    AuthenticationError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)


class AnalysisResult(BaseModel):
    """Example structured output for testing."""
    summary: str
    confidence: float


def _build_openrouter_response(
    content: str = '{"summary": "test", "confidence": 0.9}',
    model: str = "openai/gpt-4o-mini",
    prompt_tokens: int = 50,
    completion_tokens: int = 100,
) -> dict:
    """Build a mock OpenRouter API response body."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            },
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


@pytest.fixture
def request_no_parsing() -> AIRequest:
    """AIRequest without response_model (raw text response)."""
    return AIRequest(
        system_prompt="You are helpful.",
        user_message="Hello.",
        temperature=0.0,
    )


@pytest.fixture
def request_with_parsing() -> AIRequest:
    """AIRequest with response_model for structured parsing."""
    return AIRequest(
        system_prompt="You are helpful.",
        user_message="Analyze this.",
        response_model=AnalysisResult,
        temperature=0.0,
    )


def test_provider_name() -> None:
    """Provider name is 'openrouter'."""
    provider = OpenRouterProvider(api_key="test-key")
    assert provider.name == "openrouter"


def test_init_requires_api_key() -> None:
    """Provider raises ValueError if no API key is provided."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenRouterProvider(api_key="")


async def test_generate_success(request_no_parsing: AIRequest) -> None:
    """Successful response returns AIResponse with correct fields."""
    mock_response = _build_openrouter_response(content="Hello back!")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        response = await provider.generate(request_no_parsing)

    assert response.content == "Hello back!"
    assert response.parsed is None
    assert response.provider.provider_name == "openrouter"
    assert response.provider.model == "openai/gpt-4o-mini"
    assert response.usage.prompt_tokens == 50
    assert response.usage.completion_tokens == 100
    assert response.usage.total_tokens == 150
    assert response.provider.latency_ms >= 0


async def test_generate_with_parsing(request_with_parsing: AIRequest) -> None:
    """Response is parsed into the requested model."""
    mock_response = _build_openrouter_response()

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        response = await provider.generate(request_with_parsing)

    assert response.parsed is not None
    assert isinstance(response.parsed, AnalysisResult)
    assert response.parsed.summary == "test"
    assert response.parsed.confidence == 0.9


async def test_generate_with_code_fenced_response(request_with_parsing: AIRequest) -> None:
    """Responses wrapped in ```json fences are parsed correctly."""
    mock_response = _build_openrouter_response(
        content='```json\n{"summary": "ok", "confidence": 0.8}\n```',
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        response = await provider.generate(request_with_parsing)

    assert response.parsed is not None
    assert response.parsed.summary == "ok"


async def test_authentication_error(request_no_parsing: AIRequest) -> None:
    """HTTP 401 raises AuthenticationError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="Unauthorized")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="bad-key", http_client=client)
        with pytest.raises(AuthenticationError):
            await provider.generate(request_no_parsing)


async def test_rate_limit_error(request_no_parsing: AIRequest) -> None:
    """HTTP 429 raises RateLimitError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Too Many Requests")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        with pytest.raises(RateLimitError):
            await provider.generate(request_no_parsing)


async def test_http_5xx_error(request_no_parsing: AIRequest) -> None:
    """HTTP 5xx raises ProviderError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        with pytest.raises(ProviderError):
            await provider.generate(request_no_parsing)


async def test_empty_choices(request_no_parsing: AIRequest) -> None:
    """Empty choices array raises ProviderError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        with pytest.raises(ProviderError, match="empty choices"):
            await provider.generate(request_no_parsing)


async def test_model_override(request_no_parsing: AIRequest) -> None:
    """Request-level model override is used instead of default."""
    mock_response = _build_openrouter_response()

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        assert body["model"] == "anthropic/claude-3-haiku"
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(
            api_key="test-key",
            model="openai/gpt-4o-mini",
            http_client=client,
        )
        request_no_parsing.model = "anthropic/claude-3-haiku"
        response = await provider.generate(request_no_parsing)

    assert response.provider.model == "anthropic/claude-3-haiku"


async def test_timeout_error(request_no_parsing: AIRequest) -> None:
    """Timeout raises ProviderTimeoutError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Timed out", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, timeout=5.0) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        with pytest.raises(ProviderTimeoutError):
            await provider.generate(request_no_parsing)


async def test_invalid_json_response(request_with_parsing: AIRequest) -> None:
    """Non-JSON response content raises error during parsing."""
    mock_response = _build_openrouter_response(content="not json")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenRouterProvider(api_key="test-key", http_client=client)
        response = await provider.generate(request_with_parsing)
        # parse_json_response failure is caught, parsed stays None
        assert response.parsed is None
        assert response.content == "not json"
