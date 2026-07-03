"""Core domain models for the AI layer.

These models are the shared language between:
- AI providers (openrouter, ollama, etc.)
- PromptManager
- AI Orchestrator
- Business modules

No provider-specific types escape this layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token consumption for a single AI response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ProviderMetadata(BaseModel):
    """Metadata about the provider that generated a response."""

    provider_name: str
    model: str
    latency_ms: int


class AIRequest(BaseModel):
    """A fully-rendered prompt ready to send to an AI provider.

    Fields:
        system_prompt: System-level instructions for the model.
        user_message: The user's input / context for the model.
        response_model: Optional Pydantic model to parse the response into.
        model: Override the default model for this request.
        temperature: Override the default temperature.
        max_tokens: Override the default max output tokens.
    """

    system_prompt: str
    user_message: str
    response_model: type[BaseModel] | None = Field(default=None, exclude=True)
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

    class Config:
        arbitrary_types_allowed = True


class AIResponse(BaseModel):
    """Normalized response from any AI provider.

    Fields:
        content: Raw text content of the response.
        parsed: If a ``response_model`` was provided in the request and the
            content was valid JSON matching that model, this is the parsed result.
        usage: Token usage statistics.
        provider: Metadata about the provider that generated this response.
    """

    content: str
    parsed: BaseModel | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    provider: ProviderMetadata
