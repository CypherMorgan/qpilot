"""AI Infrastructure Layer.

This package provides a provider-agnostic interface for AI interactions.
Business modules must never interact with providers directly; they go
through the AI Orchestrator.

Exported public API:
    - AIRequest, AIResponse, TokenUsage, ProviderMetadata
    - AIProvider (Protocol)
    - ProviderRegistry
    - PromptManager, PromptTemplate, TemplateMetadata
"""

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.prompt_manager import PromptManager, PromptTemplate, TemplateMetadata
from app.ai.protocol import AIProvider
from app.ai.registry import ProviderRegistry

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "PromptManager",
    "PromptTemplate",
    "ProviderMetadata",
    "ProviderRegistry",
    "TemplateMetadata",
    "TokenUsage",
]
