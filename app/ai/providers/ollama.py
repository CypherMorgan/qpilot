"""Ollama provider adapter.

Communicates with a local Ollama instance using the Ollama chat API.
No Ollama SDK is required — all communication is via ``httpx``.

Configuration via environment variables:
    - ``AI__OLLAMA_BASE_URL`` — Ollama server URL (default: ``http://localhost:11434``)
    - ``AI__OLLAMA_MODEL`` — Default model name (default: ``qwen3``)
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

import httpx

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.response_validator import parse_json_response
from app.exceptions import (
    InvalidResponseError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OllamaProvider:
    """Adapter for the local Ollama chat API.

    Uses the ``/api/chat`` endpoint with ``stream: false``.
    Supports any model available in the local Ollama instance.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialise the Ollama provider.

        Args:
            base_url: Base URL of the Ollama server (without trailing slash).
            model: Default model name.
            http_client: Optional shared ``httpx.AsyncClient``.
                A default client with a 120-second timeout is created if
                none is provided (Ollama can be slow for large models).
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._http = http_client or httpx.AsyncClient(timeout=120.0)

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, request: AIRequest) -> AIResponse:
        """Send a chat request to the local Ollama instance.

        Args:
            request: The rendered prompt and configuration.

        Returns:
            A normalized ``AIResponse``.  Note that Ollama does not
            report token counts, so these will be zero.

        Raises:
            ProviderUnavailableError: If the Ollama server is unreachable.
            ProviderTimeoutError: If the request times out.
            ProviderError: For any other provider error.
        """
        start = time.monotonic()

        payload: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_message},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": request.temperature or 0.2,
                "num_predict": request.max_tokens or 4096,
            },
        }

        try:
            response = await self._http.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Is Ollama running?",
                detail={"base_url": self._base_url},
            ) from exc
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"Ollama request timed out after {self._http.timeout}s",
            ) from exc

        latency_ms = int((time.monotonic() - start) * 1000)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Ollama returned HTTP {response.status_code}",
                detail={
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            ) from exc

        data: dict[str, Any] = response.json()
        content = data.get("message", {}).get("content", "")

        # Parse structured response if a response model was requested
        parsed = None
        if request.response_model and content:
            with contextlib.suppress(InvalidResponseError):
                _, parsed = parse_json_response(content, request.response_model)

        # Ollama doesn't report token counts
        return AIResponse(
            content=content,
            parsed=parsed,
            usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            provider=ProviderMetadata(
                provider_name=self.name,
                model=request.model or self._model,
                latency_ms=latency_ms,
            ),
        )
