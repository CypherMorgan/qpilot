"""Application exception hierarchy.

All exceptions inherit from QPilotError, providing a consistent
error structure for API responses and logging.
"""

from __future__ import annotations

from typing import Any


class QPilotError(Exception):
    """Base exception for all QPilot errors."""

    def __init__(
        self,
        message: str = "",
        *,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


class ConfigurationError(QPilotError):
    """Raised when application configuration is invalid or incomplete."""


# ── AI Provider Errors ──────────────────────────────────────────


class ProviderError(QPilotError):
    """Base exception for all AI provider errors."""


class ProviderTimeoutError(ProviderError):
    """Raised when an AI provider request times out."""


class ProviderNotAvailableError(ProviderError):
    """Raised when the configured provider is not registered."""


class ProviderUnavailableError(ProviderError):
    """Raised when the provider service is unreachable or returns 5xx."""


class AuthenticationError(ProviderError):
    """Raised when the provider rejects the API key / credentials."""


class RateLimitError(ProviderError):
    """Raised when the provider returns a rate-limit response."""


class InvalidResponseError(ProviderError):
    """Raised when the provider response cannot be parsed or validated."""


# ── Prompt Errors ──────────────────────────────────────────────


class InvalidPromptError(QPilotError):
    """Raised when a prompt template is missing, malformed, or fails to render."""


# ── Generic Application Errors ─────────────────────────────────


class ValidationError(QPilotError):
    """Raised when input validation fails."""


class NotFoundError(QPilotError):
    """Raised when a requested resource does not exist."""


class StorageError(QPilotError):
    """Raised when file storage operations fail."""


class AnalysisError(QPilotError):
    """Raised when an analysis pipeline fails."""


ERROR_CODE_MAP: dict[type[QPilotError], str] = {
    ConfigurationError: "CONFIGURATION_ERROR",
    ProviderError: "PROVIDER_ERROR",
    ProviderTimeoutError: "PROVIDER_TIMEOUT",
    ProviderNotAvailableError: "PROVIDER_NOT_AVAILABLE",
    ProviderUnavailableError: "PROVIDER_UNAVAILABLE",
    AuthenticationError: "AUTHENTICATION_ERROR",
    RateLimitError: "RATE_LIMIT_ERROR",
    InvalidResponseError: "INVALID_RESPONSE_ERROR",
    InvalidPromptError: "INVALID_PROMPT_ERROR",
    ValidationError: "VALIDATION_ERROR",
    NotFoundError: "NOT_FOUND",
    StorageError: "STORAGE_ERROR",
    AnalysisError: "ANALYSIS_ERROR",
}


def get_error_code(exc: QPilotError) -> str:
    """Return the standard error code for a QPilotError subclass."""
    return ERROR_CODE_MAP.get(type(exc), "INTERNAL_ERROR")
