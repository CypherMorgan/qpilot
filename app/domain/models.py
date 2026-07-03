"""Shared domain models used across multiple feature modules."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisStatus(StrEnum):
    """Status of an analysis session."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(StrEnum):
    """Supported analysis types."""

    REQUIREMENT_ANALYSIS = "requirement-analysis"
    API_TEST_GENERATION = "api-test-generation"
    FAILURE_ANALYSIS = "failure-analysis"


class ArtifactType(StrEnum):
    """Types of uploaded artifacts."""

    REQUIREMENT = "requirement"
    OPENAPI_SPEC = "openapi_spec"
    TEST_LOG = "test_log"
    SCREENSHOT = "screenshot"
    PAGE_SOURCE = "page_source"
    OTHER = "other"


class AnalysisSessionRef(BaseModel):
    """Lightweight reference to an analysis session (used in list responses)."""

    session_id: UUID
    analysis_type: AnalysisType
    title: str | None = None
    status: AnalysisStatus
    provider: str | None = None
    total_tokens: int = 0
    latency_ms: int = 0
    created_at: datetime
    completed_at: datetime | None = None


class ProviderCallInfo(BaseModel):
    """Metadata about an AI provider call."""

    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total: int = 0
    has_more: bool = False


class ResponseMeta(BaseModel):
    """Metadata included in every API response."""

    request_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pagination: PaginationMeta | None = None
