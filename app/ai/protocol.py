"""Provider Protocol definition.

Every AI provider adapter must satisfy the ``AIProvider`` protocol.
Structural subtyping (``typing.Protocol``) is used instead of ABC so
that any class with matching method signatures satisfies the contract
— no inheritance required.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.ai.models import AIRequest, AIResponse


@runtime_checkable
class AIProvider(Protocol):
    """Contract every AI provider adapter must satisfy.

    Implementing classes must provide:
        1. A ``name`` property returning the provider identifier string.
        2. An async ``generate`` method accepting ``AIRequest`` and
           returning ``AIResponse``.
    """

    @property
    def name(self) -> str:
        """Return the provider name (e.g. ``"openrouter"``, ``"ollama"``)."""

    async def generate(self, request: AIRequest) -> AIResponse:
        """Send a prompt to the provider and return a normalized response.

        Args:
            request: The fully-rendered prompt and configuration.

        Returns:
            A normalized ``AIResponse`` with content, usage, and metadata.

        Raises:
            ProviderError: Subclasses of this for provider-specific errors.
        """
