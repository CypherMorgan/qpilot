"""Pydantic schemas for API Test Generation.

Defines the input/output contracts for the API test generation
workflow:

1. **Input**: An OpenAPI 3.x specification (JSON or YAML string)
   plus optional filters (endpoint paths to include).

2. **Output**: Metadata about the generated test suite, including
   file listing and download URL.  The actual file content is stored
   in the session's ``output_data`` and served as a ZIP download.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ── Input schema ──────────────────────────────────────────────────


class OpenApiGenerateRequest(BaseModel):
    """Request payload for the API test generation endpoint.

    The user provides an OpenAPI 3.x specification as a string
    (JSON or YAML format) and optionally filters which endpoint
    paths to generate tests for.
    """

    spec: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Raw OpenAPI 3.x specification content (JSON or YAML).",
    )
    spec_format: Literal["json", "yaml"] = Field(
        default="yaml",
        description="Format of the provided spec: 'json' or 'yaml'.",
    )
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for the generation session.",
    )
    paths: list[str] | None = Field(
        default=None,
        description=(
            "Optional list of endpoint paths to generate tests for. "
            "If omitted, tests are generated for all paths. "
            "Example: ['/pets', '/users']"
        ),
    )
    context: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional additional context (e.g. tech stack, auth setup notes).",
    )


# ── Output models ─────────────────────────────────────────────────


class GeneratedFile(BaseModel):
    """Metadata about a single generated test file."""

    filename: str = Field(description="File name, e.g. 'test_pets.py'.")
    path: str = Field(description="Relative path within the archive, e.g. 'generated-tests/test_pets.py'.")
    size: int = Field(default=0, description="File size in bytes.")
    content: str = Field(default="", description="File content (embedded in API response for preview, not stored in list).")


class EndpointGenInfo(BaseModel):
    """Summary of test generation for a single endpoint."""

    path: str = Field(description="The endpoint path.")
    method: str = Field(description="HTTP method (lowercase).")
    tests_generated: int = Field(default=0, description="Number of test functions generated for this endpoint.")


class OpenApiGenerateResponse(BaseModel):
    """API response after a successful test generation."""

    session_id: UUID = Field(description="ID of the analysis session.")
    status: str = Field(description="Current status of the session.")
    spec_title: str = Field(default="", description="Title from the OpenAPI spec.")
    spec_version: str = Field(default="", description="Version from the OpenAPI spec.")
    endpoint_count: int = Field(default=0, description="Number of endpoints processed.")
    files: list[GeneratedFile] = Field(
        default_factory=list,
        description="List of generated test files (metadata only, no content in list).",
    )
    endpoints: list[EndpointGenInfo] = Field(
        default_factory=list,
        description="Per-endpoint generation summary.",
    )
    download_url: str = Field(default="", description="URL to download the ZIP archive of generated tests.")
    provider: str | None = Field(default=None, description="AI provider used.")
    model: str | None = Field(default=None, description="AI model used.")
    total_tokens: int = Field(default=0, description="Total tokens consumed across all AI calls.")
    latency_ms: int = Field(default=0, description="Total AI call duration in milliseconds.")


class OpenApiSessionListItem(BaseModel):
    """Lightweight summary for listing past generation sessions."""

    session_id: UUID
    title: str | None = None
    spec_title: str | None = None
    spec_version: str | None = None
    endpoint_count: int = 0
    file_count: int = 0
    status: str
    provider: str | None = None
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime
