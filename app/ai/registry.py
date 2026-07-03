"""Provider Registry.

Maps provider names (e.g. ``"openrouter"``, ``"ollama"``) to their
adapter instances.  Business modules never instantiate providers directly
— they call ``ProviderRegistry.get(name)``.
"""

from __future__ import annotations

from app.ai.protocol import AIProvider


class ProviderRegistry:
    """Maps provider names to adapter instances.

    Usage::

        registry = ProviderRegistry()
        registry.register("openrouter", OpenRouterProvider(api_key=...))
        registry.register("ollama", OllamaProvider())

        provider = registry.get("openrouter")
        response = await provider.generate(request)
    """

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, name: str, provider: AIProvider) -> None:
        """Register a provider under the given name.

        Args:
            name: Provider identifier (e.g. ``"openrouter"``).
            provider: An object satisfying the ``AIProvider`` protocol.

        Raises:
            ValueError: If ``name`` is already registered.
        """
        if name in self._providers:
            raise ValueError(f"Provider '{name}' is already registered")
        self._providers[name] = provider

    def get(self, name: str) -> AIProvider:
        """Retrieve a registered provider by name.

        Args:
            name: Provider identifier.

        Returns:
            The registered provider instance.

        Raises:
            ProviderUnavailableError: If the provider is not registered.
        """
        if name not in self._providers:
            from app.exceptions import ProviderUnavailableError

            raise ProviderUnavailableError(
                f"Unknown provider: '{name}'. "
                f"Available: {list(self._providers.keys())}",
            )
        return self._providers[name]

    @property
    def available(self) -> list[str]:
        """Return the list of registered provider names."""
        return list(self._providers.keys())
