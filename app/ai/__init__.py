"""AI Infrastructure Layer.

This package provides a provider-agnostic interface for AI interactions.
Business modules must never interact with providers directly; they go
through the AI Orchestrator.

Exported public API:
    - AIRequest, AIResponse, TokenUsage, ProviderMetadata
    - AIProvider (Protocol)
    - ProviderRegistry
    - ResilientProvider, HealthTracker
    - PromptManager, PromptTemplate, TemplateMetadata
"""

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.prompt_manager import PromptManager, PromptTemplate, TemplateMetadata
from app.ai.protocol import AIProvider
from app.ai.registry import ProviderRegistry
from app.ai.resilience import HealthTracker, ResilientProvider

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "HealthTracker",
    "PromptManager",
    "PromptTemplate",
    "ProviderMetadata",
    "ProviderRegistry",
    "ResilientProvider",
    "TemplateMetadata",
    "TokenUsage",
]
