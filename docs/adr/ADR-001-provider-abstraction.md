# ADR-001: AI Provider Abstraction

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-01 |
| **Last Updated** | 2026-07-02 |
| **Author(s)** | QPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

QPilot provides AI-powered analysis across multiple feature modules (Requirement Analysis, API Test Generation, Failure Analysis). These modules need to send prompts to AI models and receive structured responses.

The platform has chosen **OpenRouter** as its default MVP provider (OpenAI-compatible API, no age verification, free-tier models, single-access to multiple open models), but the product vision requires:
- **Provider agnosticism** — users should choose their preferred provider through configuration
- **Local AI support** — Ollama support for offline/self-hosted use (post-MVP)
- **Extensibility** — adding a new provider should not require changes to business logic
- **Free-tier accessibility** — the platform must work without requiring paid subscriptions

Without an explicit abstraction, each feature module would need to:
1. Know which provider is configured
2. Import provider-specific SDKs
3. Handle provider-specific error formats
4. Parse and validate provider-specific response formats
5. Track token usage with provider-specific APIs

This coupling would make provider switching a multi-module refactor and make unit testing impossible without real API keys.

---

## Problem Statement

How can QPilot support multiple AI providers (OpenRouter, Ollama, OpenAI, Anthropic Claude, Google Gemini, Groq) without coupling business logic to any specific provider's SDK, API format, or authentication mechanism?

More specifically:

1. **Feature modules must not know which provider they're using.** A module should call `orchestrator.analyze(...)` and receive a structured result, regardless of whether the backend provider is OpenRouter, Ollama, OpenAI, Claude, or something else.

2. **Adding a new provider must not require changes to business logic.** Adding Claude support means writing a new adapter class and registering it — nothing more.

3. **Testing should not require real API keys.** Any component that depends on AI should be testable with a mock provider.

4. **Token usage and latency must be tracked uniformly.** Every provider reports token counts and latency in the same response model, enabling future analytics.

---

## Decision

We will implement a **Provider Abstraction** consisting of three layers:

```
┌────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌────────────────────────────────────────────────────────┐│
│  │           AIProvider (Protocol)                         ││
│  │  async def generate(request: AIRequest)                 ││
│  │                     -> AIResponse                       ││
│  └──────────────────────────┬─────────────────────────────┘│
│                             │ uses                         │
│  ┌──────────────────────────▼─────────────────────────────┐│
│  │                ProviderRegistry                         ││
│  │  Maps "openrouter" → OpenRouterProvider                ││
│  │  Maps "ollama" → OllamaProvider                        ││
│  │  get(name: str) -> AIProvider                          ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
                             │
                             │ implements
┌────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │  OpenRouter  │ │    Ollama    │ │  OpenAI / Claude /   ││
│  │  Provider    │ │  Provider    │ │  Gemini / Groq (future)│
│  └──────────────┘ └──────────────┘ └──────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

### 1. Provider Interface (Application Layer)

The interface is defined as a `typing.Protocol` (structural subtyping) rather than an abstract base class:

```python
# app/ai/protocol.py

from typing import Protocol, Any
from pydantic import BaseModel


class TokenUsage(BaseModel):
    """Token consumption for an AI response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ProviderMetadata(BaseModel):
    """Metadata about the provider that generated a response."""

    provider_name: str
    model: str
    latency_ms: int


class AIRequest(BaseModel):
    """A fully-rendered prompt ready to send to an AI provider."""

    system_prompt: str
    user_message: str
    response_model: type[BaseModel] | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class AIResponse(BaseModel):
    """Normalized response from any AI provider."""

    content: str
    parsed: BaseModel | None = None
    usage: TokenUsage
    provider: ProviderMetadata


class AIProvider(Protocol):
    """Contract every AI provider adapter must satisfy."""

    @property
    def name(self) -> str: ...

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse: ...
```

**Why `Protocol` instead of `ABC`?**
- Structural subtyping means any class with the right method signatures satisfies the contract — no need to inherit from a base class
- Easier to create mock providers in tests (just implement the methods)
- Follows Python's "duck typing" philosophy while still providing type safety
- Providers could in theory be implemented in other languages via FFI (overkill, but illustrates the flexibility)

### 2. Provider Registry (Application Layer)

```python
# app/ai/registry.py

from app.ai.protocol import AIProvider


class ProviderRegistry:
    """Maps provider names to adapter instances."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, name: str, provider: AIProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> AIProvider:
        if name not in self._providers:
            from app.ai.errors import ProviderUnavailableError

            raise ProviderUnavailableError(
                f"Unknown provider: '{name}'. "
                f"Available: {list(self._providers.keys())}"
            )
        return self._providers[name]

    @property
    def available(self) -> list[str]:
        return list(self._providers.keys())
```

The registry is populated at application startup during DI wiring:

```python
# app/main.py (representative)

registry = ProviderRegistry()
registry.register("openrouter", OpenRouterProvider(api_key=config.ai.openrouter_api_key))
registry.register("ollama", OllamaProvider(base_url=config.ai.ollama_base_url))
```

### 3. Provider Adapters (Infrastructure Layer)

Each adapter implements the `AIProvider` protocol for a specific AI provider.  All
providers talk to their respective APIs via `httpx` — no SDKs leak into the
infrastructure layer.

#### OpenRouterProvider (MVP — default)

```python
# app/ai/providers/openrouter.py

import httpx
from app.ai.protocol import AIProvider, AIRequest, AIResponse, TokenUsage, ProviderMetadata


class OpenRouterProvider:
    """Adapter for the OpenRouter API (OpenAI-compatible)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._http = http_client or httpx.AsyncClient(timeout=60.0)

    @property
    def name(self) -> str:
        return "openrouter"

    async def generate(self, request: AIRequest) -> AIResponse:
        import time
        start = time.monotonic()

        response = await self._http.post(
            self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": request.model or self._model,
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_message},
                ],
                "temperature": request.temperature or 0.2,
                "max_tokens": request.max_tokens or 4096,
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.monotonic() - start) * 1000)
        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage_data = data.get("usage", {})

        parsed = None
        if request.response_model and content:
            parsed = request.response_model.model_validate_json(content)

        return AIResponse(
            content=content,
            parsed=parsed,
            usage=TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
            provider=ProviderMetadata(
                provider_name=self.name,
                model=request.model or self._model,
                latency_ms=latency_ms,
            ),
        )
```

#### OllamaProvider (second provider — validates abstraction)

```python
# app/ai/providers/ollama.py

import httpx
from app.ai.protocol import AIProvider, AIRequest, AIResponse, TokenUsage, ProviderMetadata


class OllamaProvider:
    """Adapter for local Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._http = http_client or httpx.AsyncClient(timeout=120.0)

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, request: AIRequest) -> AIResponse:
        import time
        start = time.monotonic()

        response = await self._http.post(
            f"{self._base_url}/api/chat",
            json={
                "model": request.model or self._model,
                "messages": [
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_message},
                ],
                "stream": False,
                "options": {
                    "temperature": request.temperature or 0.2,
                    "num_predict": request.max_tokens or 4096,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        latency_ms = int((time.monotonic() - start) * 1000)
        content = data.get("message", {}).get("content", "")

        parsed = None
        if request.response_model and content:
            parsed = request.response_model.model_validate_json(content)

        return AIResponse(
            content=content,
            parsed=parsed,
            usage=TokenUsage(
                prompt_tokens=0,   # Ollama doesn't report token counts
                completion_tokens=0,
                total_tokens=0,
            ),
            provider=ProviderMetadata(
                provider_name=self.name,
                model=request.model or self._model,
                latency_ms=latency_ms,
            ),
        )
```

### 4. AI Orchestrator Consumption

Feature modules never interact with providers directly. They go through the AI Orchestrator:

```python
# app/ai/orchestrator.py

class AIOrchestrator:
    def __init__(
        self,
        prompt_manager: PromptManager,
        provider_registry: ProviderRegistry,
        provider_name: str,
    ) -> None:
        self._prompts = prompt_manager
        self._provider = provider_registry.get(provider_name)

    async def analyze(
        self,
        analysis_type: str,
        context: dict[str, Any],
        response_model: type[BaseModel],
    ) -> AnalysisResult:
        # 1. Load and render the prompt template
        prompt = self._prompts.load(analysis_type, context)

        # 2. Build the request
        request = AIRequest(
            system_prompt=prompt.system_prompt,
            user_message=prompt.user_message,
            response_model=response_model,
        )

        # 3. Call the provider
        response = await self._provider.generate(request)

        # 4. Return normalized result
        return AnalysisResult(
            content=response.parsed or response.content,
            provider=response.provider.provider_name,
            model=response.provider.model,
            tokens=response.usage.total_tokens,
            latency_ms=response.provider.latency_ms,
            status="error" if response.parsed is None and not response.content else "success",
            error=None,
        )
```

---

## Alternatives Considered

### Alternative A: Direct SDK Usage in Modules (Rejected)

Each feature module imports and calls the AI provider SDK directly.

```python
# In the Requirement Analysis service:
import google.generativeai as genai

response = genai.GenerativeModel(...).generate_content(...)
```

| Dimension | Direct SDK | Provider Abstraction (Chosen) |
|---|---|---|
| **Provider switching** | Rewrite every module | Config change + new adapter |
| **Testing without API keys** | Impossible without mocking | Mock the provider interface |
| **Token tracking** | Manual, duplicated per module | Centralized in provider adapter |
| **Error handling** | Per-module try/except | Centralized in provider adapter |
| **Code required per new provider** | N modules × 1 provider = N changes | 1 adapter + 1 registry entry |
| **Lines of code** | Less for MVP with 1 provider | Slightly more — interface + adapter + registry |

**Decision:** Rejected. The abstraction cost is small (one Protocol class, one Registry class), and the benefits compound with every additional provider or module. Using OpenRouter's SDK directly would create a hidden dependency that would be painful to untangle later.

### Alternative B: Provider Abstraction as Abstract Base Class (Rejected)

```python
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    async def analyze(self, request: PromptRequest) -> ProviderResponse: ...
```

| Dimension | ABC | Protocol (Chosen) |
|---|---|---|
| **Coupling** | Providers must inherit from BaseProvider | Providers only need to match the signature |
| **Testing** | Mock must inherit from BaseProvider | Mock just needs the right methods |
| **Multiple inheritance** | Complicated (MRO) | Protocol composes naturally |
| **Type checking** | Works with MyPy | Works with MyPy (structural typing support) |
| **Python philosophy** | "Make everything inherit" | "If it walks like a duck..." |

**Decision:** Protocol over ABC. Structural subtyping is more Pythonic and creates looser coupling. A provider doesn't need to "be a BaseProvider" — it just needs to "provide the analyze method."

### Alternative C: Single Provider with No Abstraction (Rejected)

Build for OpenRouter only. If a user wants Claude, that's a separate deployment.

| Dimension | Single Provider | Abstraction (Chosen) |
|---|---|---|
| **Initial speed** | Fastest — no interface to design | Requires interface design upfront |
| **Provider switching** | Rebuild application | Config change |
| **Ollama/local support** | Impossible | Config change + local adapter |
| **Portfolio signal** | "Locked into Google" | "Designed for extensibility" |
| **Product vision alignment** | Contradicts provider agnosticism | Directly supports it |

**Decision:** Rejected. Our vision explicitly requires provider agnosticism. Building for one provider and retrofitting abstraction later is more expensive than designing it upfront.

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **Abstraction overhead** vs **Provider coupling** | The abstraction adds ~50 lines of shared code (Protocol + Registry). In exchange, every new provider costs one adapter class instead of N module changes. The break-even point is 1 provider switch or 2 providers. |
| **Protocol flexibility** vs **Explicit contract enforcement** | Protocols provide structural typing but don't enforce method signatures at instantiation time (only at call time). Mitigated by MyPy strict mode catching mismatches at CI time. |
| **Normalized response model** vs **Provider-specific features** | A normalized model (ProviderResponse) means we can't expose every feature of every provider. For example, Gemini's safety ratings or Claude's citation metadata would be lost. Mitigation: ProviderResponse includes an optional `raw: dict[str, Any]` field for provider-specific extras. |
| **Async-by-default** vs **Sync provider support** | The interface is async, which is natural for FastAPI. If a provider SDK is sync-only, the adapter wraps it in `asyncio.to_thread()`. This adds negligible complexity. |

---

## Consequences

### Positive

1. **Zero business logic changes to add a provider.** New provider = new adapter class + one registry registration.
2. **Full testability.** Every component above the provider layer can be tested without API keys.
3. **Consistent observability.** Token usage, latency, and error rates are captured in the same format regardless of provider.
4. **Configuration-driven.** Provider selection is a config value, not a code change.
5. **Portfolio signal.** This abstraction is a clear differentiator from "AI wrapper" projects.

### Negative

1. **Slightly more upfront code.** The Protocol, Registry, and adapter layers add ~80-120 lines of infrastructure code.
2. **Provider-specific features need escape hatches.** If a provider has unique capabilities (e.g., Gemini's grounding, Claude's extended thinking), the normalized model needs extension points.
3. **Async requirement.** Sync-only provider SDKs need thread-pool wrapping.

### Neutral

1. **Provider interface may evolve.** As we add vision/image analysis, the `PromptRequest` model may need `image: bytes | None` and a `mime_type: str`. The interface should be designed for evolution.

---

## Implementation Impact

### New Files

```
app/
└── ai/
    ├── __init__.py
    ├── models.py             # AIRequest, AIResponse, TokenUsage, ProviderMetadata
    ├── protocol.py           # AIProvider Protocol
    ├── registry.py           # ProviderRegistry
    ├── errors.py             # AI-specific error hierarchy
    ├── response_validator.py # Response content validation
    ├── prompt_manager.py     # PromptManager, PromptTemplate, TemplateMetadata
    └── providers/
        ├── __init__.py
        ├── openrouter.py     # OpenRouterProvider (MVP — default)
        └── ollama.py         # OllamaProvider (second provider — validates abstraction)
```

### Modified Files

- `app/ai/orchestrator.py` — consumes provider through the interface
- `app/main.py` — registers providers at startup, wires registry
- `app/config.py` — add OpenRouter config fields, update provider list
- `app/exceptions.py` — update AI error hierarchy
- `pyproject.toml` — remove `google-generativeai` dependency (using httpx for all providers)
- `.env.example` — set `AI_PROVIDER=openrouter`, add `OPENROUTER_API_KEY`

### Migration

No migration needed — this is the initial implementation.

---

## Testing Impact

### Unit Tests

| Test | What it validates | Mock boundary |
|---|---|---|
| `test_provider_protocol` | Protocol works with structural subtyping | Minimal mock class |
| `test_provider_registry` | Registration, retrieval, unknown provider error | Mock providers |
| `test_provider_response_validation` | Response model validates correctly | Raw JSON fixtures |
| `test_orchestrator_uses_provider` | Orchestrator calls provider.generate() | Mock provider |
| `test_openrouter_provider` | OpenRouter adapter with mocked HTTP | `httpx.MockTransport` |
| `test_ollama_provider` | Ollama adapter with mocked HTTP | `httpx.MockTransport` |

### Test Fixtures

```python
# tests/conftest.py

@pytest.fixture
def mock_provider():
    """A provider that returns predictable responses without real API calls."""

    class MockProvider:
        @property
        def name(self) -> str:
            return "mock"

        async def generate(self, request: AIRequest) -> AIResponse:
            return AIResponse(
                content='{"result": "mocked"}',
                parsed=request.response_model(**{"result": "mocked"}),
                usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                provider=ProviderMetadata(
                    provider_name="mock",
                    model="mock-model",
                    latency_ms=5,
                ),
            )

    return MockProvider()


@pytest.fixture
def registry(mock_provider):
    reg = ProviderRegistry()
    reg.register("mock", mock_provider)
    return reg
```

---

## Future Evolution

| Phase | Change | Impact |
|---|---|---|
| **Post-MVP: OpenAI support** | New `OpenAIProvider` + registry entry | Zero changes to business logic |
| **Post-MVP: Anthropic Claude support** | New `ClaudeProvider` + registry entry | Zero changes to business logic |
| **Post-MVP: Google Gemini support** | New `GeminiProvider` + registry entry | Zero changes to business logic |
| **Post-MVP: Groq support** | New `GroqProvider` + registry entry | Zero changes to business logic |
| **Post-MVP: Multi-provider routing** | `RouterProvider` that selects by analysis type | New adapter that wraps other adapters |
| **Post-MVP: Fallback chains** | `FallbackProvider` — try provider A, fall back to B | New adapter that wraps other adapters |
| **Post-MVP: Response caching** | `CachedProvider` — check cache before calling | New adapter with Redis backend |
| **Post-MVP: Rate limiting** | Provider adapter implements rate limiting | Within adapter, transparent to callers |
| **Phase 3: Vision analysis** | Add `image` field to `AIRequest` | Interface change, updates all adapters |

Each of these future changes adds an *adapter* — it never modifies business logic.

---

## Decision Rationale Summary

The Provider Abstraction is **justified** because:

1. **It solves a real problem today** — feature modules must be testable without API keys
2. **It aligns with the product vision** — provider agnosticism is a stated requirement
3. **The cost is minimal** — ~50 lines of shared code + one adapter per provider
4. **The break-even is immediate** — even with one provider, the testability benefit justifies the abstraction
5. **It demonstrates architectural maturity** — this is the single strongest signal that QPilot is not "another AI wrapper"

**Abstraction question answers (per engineering rule):**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Coupling of business logic to specific AI provider SDKs |
| **Why is this necessary today?** | Without it, we can't unit test feature modules without real API keys |
| **What simpler alternative exists?** | Direct SDK usage with mocking via `unittest.mock.patch` |
| **Why was that rejected?** | Monkey-patching SDKs is brittle, doesn't scale to multiple providers, and provides no centralized token tracking |
| **How does this help evolution?** | Adding a provider = new adapter class; switching providers = config change |

---

## Compliance with Architecture Categories

| Component | Category | Justification |
|---|---|---|
| `AIProvider` (Protocol) | **Application** | Application code depends on this interface |
| `ProviderRegistry` | **Application** | Application code uses the registry to obtain providers |
| `AIRequest` | **Application** | Request model used by application/orchestration layer |
| `AIResponse` | **Application** | Response model used by application/orchestration layer |
| `PromptManager` | **Application** | Renders prompts from templates; used by orchestrator |
| `OpenRouterProvider` | **Infrastructure** | Implements a contract; knows about HTTP, JSON, API formats |
| `OllamaProvider` | **Infrastructure** | Implements a contract; knows about HTTP, JSON, API formats |
| `MockProvider` (test) | **Test** | Not part of production code |

The Application layer defines the contract. The Infrastructure layer fulfills it. Domain layer is unaffected — providers operate at the infrastructure level.
