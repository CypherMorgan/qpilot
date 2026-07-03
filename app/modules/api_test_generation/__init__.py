"""API Test Generation Module.

Provides AI-powered generation of PyTest API test suites from
OpenAPI 3.x specifications.  Parses the spec programmatically to
extract endpoints and schemas, then uses AI to generate intelligent
test cases with proper assertions, edge cases, and error handling.

Public API:
    - ``OpenApiGenerateRequest`` — input schema for the generation endpoint
    - ``OpenApiGenerateResponse`` — output schema with session info & files
    - ``router`` — FastAPI router with generation endpoints
    - ``ApiTestGenerationService`` — business logic orchestrator
"""

from app.modules.api_test_generation.models import (
    GeneratedFile,
    OpenApiGenerateRequest,
    OpenApiGenerateResponse,
    OpenApiSessionListItem,
)
from app.modules.api_test_generation.router import router
from app.modules.api_test_generation.service import ApiTestGenerationService

__all__ = [
    "ApiTestGenerationService",
    "GeneratedFile",
    "OpenApiGenerateRequest",
    "OpenApiGenerateResponse",
    "OpenApiSessionListItem",
    "router",
]
