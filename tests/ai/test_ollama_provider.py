"""Tests for OllamaProvider."""

import httpx
import pytest
from pydantic import BaseModel

from app.ai.models import AIRequest
from app.ai.providers.ollama import OllamaProvider
from app.exceptions import (
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class AnalysisResult(BaseModel):
    """Example structured output for testing."""
    summary: str
    confidence: float


def _build_ollama_response(
    content: str = '{"summary": "test", "confidence": 0.9}',
    model: str = "qwen3",
) -> dict:
    """Build a mock Ollama /api/chat response."""
    return {
        "model": model,
        "created_at": "2026-07-02T00:00:00Z",
        "message": {
            "role": "assistant",
            "content": content,
        },
        "done": True,
        "total_duration": 1_000_000_000,
    }


@pytest.fixture
def request_no_parsing() -> AIRequest:
    """AIRequest without response_model."""
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
    """Provider name is 'ollama'."""
    provider = OllamaProvider()
    assert provider.name == "ollama"


async def test_generate_success(request_no_parsing: AIRequest) -> None:
    """Successful response returns AIResponse with correct fields."""
    mock_response = _build_ollama_response(content="Hello back!")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(http_client=client)
        response = await provider.generate(request_no_parsing)

    assert response.content == "Hello back!"
    assert response.parsed is None
    assert response.provider.provider_name == "ollama"
    assert response.provider.model == "qwen3"
    assert response.usage.total_tokens == 0
    assert response.provider.latency_ms >= 0


async def test_generate_with_parsing(request_with_parsing: AIRequest) -> None:
    """Response is parsed into the requested model."""
    mock_response = _build_ollama_response()

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(http_client=client)
        response = await provider.generate(request_with_parsing)

    assert response.parsed is not None
    assert isinstance(response.parsed, AnalysisResult)
    assert response.parsed.summary == "test"
    assert response.parsed.confidence == 0.9


async def test_connection_refused(request_no_parsing: AIRequest) -> None:
    """Connection refused raises ProviderUnavailableError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(base_url="http://localhost:1", http_client=client)
        with pytest.raises(ProviderUnavailableError, match="Cannot connect"):
            await provider.generate(request_no_parsing)


async def test_timeout_error(request_no_parsing: AIRequest) -> None:
    """Timeout raises ProviderTimeoutError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Timed out", request=request)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, timeout=5.0) as client:
        provider = OllamaProvider(http_client=client)
        with pytest.raises(ProviderTimeoutError):
            await provider.generate(request_no_parsing)


async def test_http_error(request_no_parsing: AIRequest) -> None:
    """HTTP error raises ProviderError."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(http_client=client)
        with pytest.raises(ProviderError):
            await provider.generate(request_no_parsing)


async def test_empty_message(request_no_parsing: AIRequest) -> None:
    """Empty message content is handled gracefully."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "model": "qwen3",
            "message": {"role": "assistant", "content": ""},
            "done": True,
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(http_client=client)
        response = await provider.generate(request_no_parsing)

    assert response.content == ""


async def test_code_fenced_response(request_with_parsing: AIRequest) -> None:
    """Code-fenced responses are parsed correctly."""
    mock_response = _build_ollama_response(
        content='```json\n{"summary": "ok", "confidence": 0.8}\n```',
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(http_client=client)
        response = await provider.generate(request_with_parsing)

    assert response.parsed is not None
    assert response.parsed.summary == "ok"
