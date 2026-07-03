"""Tests for AIProvider Protocol structural subtyping."""

from typing import Protocol

from app.ai.models import AIRequest, AIResponse
from app.ai.protocol import AIProvider


def test_protocol_is_typeable() -> None:
    """AIProvider is a Protocol, not an ABC."""
    assert issubclass(AIProvider, Protocol)


def test_class_with_correct_signature_satisfies_protocol() -> None:
    """Any class with ``name`` and ``generate`` satisfies AIProvider."""
    # This class has the right shape — protocol check at runtime
    class GoodProvider:
        @property
        def name(self) -> str:
            return "good"

        async def generate(self, request: AIRequest) -> AIResponse:
            from app.ai.models import ProviderMetadata, TokenUsage
            return AIResponse(
                content="ok",
                usage=TokenUsage(),
                provider=ProviderMetadata(
                    provider_name="good",
                    model="m",
                    latency_ms=0,
                ),
            )

    provider = GoodProvider()
    # runtime_checkable allows isinstance check
    assert isinstance(provider, AIProvider)


def test_class_missing_generate_does_not_satisfy_protocol() -> None:
    """A class without ``generate`` should not pass isinstance check."""

    class BadProvider:
        @property
        def name(self) -> str:
            return "bad"

    provider = BadProvider()
    assert not isinstance(provider, AIProvider)


def test_class_missing_name_does_not_satisfy_protocol() -> None:
    """A class without ``name`` property should not pass isinstance check."""

    class BadProvider:
        async def generate(self, request: AIRequest) -> AIResponse:
            from app.ai.models import ProviderMetadata, TokenUsage
            return AIResponse(
                content="ok",
                usage=TokenUsage(),
                provider=ProviderMetadata(
                    provider_name="bad",
                    model="m",
                    latency_ms=0,
                ),
            )

    provider = BadProvider()
    assert not isinstance(provider, AIProvider)
