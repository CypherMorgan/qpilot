"""Tests for ProviderRegistry."""

import pytest

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.registry import ProviderRegistry
from app.exceptions import ProviderUnavailableError


class SimpleProvider:
    """Minimal provider for registry tests."""

    def __init__(self, name: str = "simple") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            content="ok",
            usage=TokenUsage(),
            provider=ProviderMetadata(
                provider_name=self._name,
                model="m",
                latency_ms=0,
            ),
        )


def test_registry_register_and_get() -> None:
    """A registered provider can be retrieved by name."""
    registry = ProviderRegistry()
    provider = SimpleProvider()
    registry.register("simple", provider)
    retrieved = registry.get("simple")
    assert retrieved is provider
    assert retrieved.name == "simple"


def test_registry_get_unknown_raises() -> None:
    """Getting an unregistered provider raises ProviderUnavailableError."""
    registry = ProviderRegistry()
    with pytest.raises(ProviderUnavailableError):
        registry.get("nonexistent")


def test_registry_available() -> None:
    """Available returns the list of registered names."""
    registry = ProviderRegistry()
    assert registry.available == []

    registry.register("a", SimpleProvider("a"))
    registry.register("b", SimpleProvider("b"))
    assert "a" in registry.available
    assert "b" in registry.available


def test_registry_duplicate_raises() -> None:
    """Registering the same name twice raises ValueError."""
    registry = ProviderRegistry()
    registry.register("dup", SimpleProvider())
    with pytest.raises(ValueError, match="already registered"):
        registry.register("dup", SimpleProvider())


def test_registry_mock_provider(mock_provider) -> None:
    """Mock provider fixture works through the registry."""
    registry = ProviderRegistry()
    registry.register("mock", mock_provider)
    assert registry.get("mock").name == "mock"
