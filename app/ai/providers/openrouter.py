"""OpenRouter provider adapter.

Communicates with the OpenRouter API (OpenAI-compatible chat
completions endpoint) using ``httpx``.  No OpenRouter-specific SDK
is required.

Configuration via environment variables:
    - ``AI__OPENROUTER_API_KEY`` — API key (required)
    - ``AI__OPENROUTER_MODEL`` — Model name (default: ``openai/gpt-4o-mini``)
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

import httpx

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.response_validator import parse_json_response
from app.exceptions import (
    AuthenticationError,
    InvalidResponseError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)


class OpenRouterProvider:
    """Adapter for the OpenRouter API (OpenAI-compatible)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialise the OpenRouter provider.

        Args:
            api_key: OpenRouter API key.
            model: Default model identifier.
            http_client: Optional shared ``httpx.AsyncClient``.
                A default client with a 60-second timeout is created if
                none is provided.
        """
        if not api_key:
            raise ValueError("OpenRouter API key is required")

        self._api_key = api_key
        self._model = model
        self._http = http_client or httpx.AsyncClient(timeout=60.0)

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(self, request: AIRequest) -> AIResponse:
        """Send a chat completion request to OpenRouter.

        Args:
            request: The rendered prompt and configuration.

        Returns:
            A normalized ``AIResponse`` with content, optional parsed
            model, token usage, and provider metadata.

        Raises:
            AuthenticationError: If the API key is invalid.
            RateLimitError: If rate-limited by OpenRouter.
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
            "temperature": request.temperature or 0.2,
            "max_tokens": request.max_tokens or 4096,
        }

        try:
            response = await self._http.post(
                self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/qpilot",  # OpenRouter ranking
                },
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"OpenRouter request timed out after {self._http.timeout}s",
            ) from exc

        latency_ms = int((time.monotonic() - start) * 1000)

        if response.status_code == 401:
            raise AuthenticationError(
                "OpenRouter authentication failed. Check your API key.",
            )

        if response.status_code == 429:
            raise RateLimitError(
                "OpenRouter rate limit exceeded. Try again later.",
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"OpenRouter returned HTTP {response.status_code}",
                detail={
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            ) from exc

        data: dict[str, Any] = response.json()

        # Extract response content
        choices = data.get("choices", [])
        if not choices:
            raise ProviderError(
                "OpenRouter returned an empty choices array",
                detail={"response": data},
            )

        content = choices[0].get("message", {}).get("content", "")

        # Parse structured response if a response model was requested
        parsed = None
        if request.response_model and content:
            with contextlib.suppress(InvalidResponseError):
                _, parsed = parse_json_response(content, request.response_model)

        # Extract usage information
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

        return AIResponse(
            content=content,
            parsed=parsed,
            usage=usage,
            provider=ProviderMetadata(
                provider_name=self.name,
                model=request.model or self._model,
                latency_ms=latency_ms,
            ),
        )
