"""Shared test fixtures for API Test Generation module tests.

Sets test environment variables at module level (before app imports)
to ensure tests use an in-memory SQLite database and don't require
a running PostgreSQL instance.
"""

from __future__ import annotations

import os

# ═══════════════════════════════════════════════════════════════════════
# Test environment — must be set before any app imports
# ═══════════════════════════════════════════════════════════════════════
os.environ.setdefault("AI__OPENROUTER_API_KEY", "test-key-for-unit-tests")
os.environ.setdefault("AI__PROVIDER", "openrouter")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")

from typing import Any

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai import AIRequest, AIResponse, PromptManager, PromptTemplate, ProviderRegistry
from app.ai.models import ProviderMetadata
from app.ai.models import TokenUsage as UsageMetadata
from app.modules.api_test_generation.models import OpenApiGenerateRequest
from app.modules.api_test_generation.spec_parser import (
    ExtractedEndpoint,
    ExtractedParameter,
    ExtractedProperty,
    ExtractedRequestBody,
    ExtractedResponse,
    ExtractedSchema,
    ParsedSpec,
    SecurityScheme,
)

# ── Test data ──────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a test fixture file content."""
    path = FIXTURES_DIR / name
    return path.read_text(encoding="utf-8")


# ── Sample parsed spec ────────────────────────────────────────────


@pytest.fixture
def petstore_yaml() -> str:
    """Returns the raw petstore.yaml content."""
    return load_fixture("petstore.yaml")


@pytest.fixture
def petstore_parsed() -> ParsedSpec:
    """Returns a pre-parsed petstore spec structure."""
    return ParsedSpec(
        title="Pet Store API",
        version="1.0.0",
        description="A sample API for managing pets",
        servers=["https://api.petstore.example.com/v1"],
        endpoints=[
            ExtractedEndpoint(
                path="/pets",
                method="get",
                summary="List all pets",
                description="Returns a list of all pets in the store",
                operation_id="listPets",
                tags=["pets"],
                parameters=[
                    ExtractedParameter(
                        name="limit",
                        location="query",
                        required=False,
                        schema_type="integer",
                        description="Maximum number of pets to return",
                    ),
                    ExtractedParameter(
                        name="offset",
                        location="query",
                        required=False,
                        schema_type="integer",
                        description="Number of pets to skip",
                    ),
                ],
                request_body=None,
                responses={
                    "200": ExtractedResponse(
                        status_code="200",
                        description="A list of pets",
                        content_type="application/json",
                        schema_ref="Pet",
                    ),
                },
                deprecated=False,
            ),
            ExtractedEndpoint(
                path="/pets",
                method="post",
                summary="Create a pet",
                description="Add a new pet to the store",
                operation_id="createPet",
                tags=["pets"],
                parameters=[],
                request_body=ExtractedRequestBody(
                    required=True,
                    content_type="application/json",
                    schema_ref="NewPet",
                    description=None,
                ),
                responses={
                    "201": ExtractedResponse(
                        status_code="201",
                        description="Pet created successfully",
                        content_type="application/json",
                        schema_ref="Pet",
                    ),
                    "400": ExtractedResponse(
                        status_code="400",
                        description="Invalid input",
                        content_type=None,
                        schema_ref=None,
                    ),
                },
                deprecated=False,
            ),
            ExtractedEndpoint(
                path="/pets/{petId}",
                method="get",
                summary="Get a pet by ID",
                description="Returns a single pet by its ID",
                operation_id="getPetById",
                tags=["pets"],
                parameters=[
                    ExtractedParameter(
                        name="petId",
                        location="path",
                        required=True,
                        schema_type="integer",
                        description="The ID of the pet to retrieve",
                    ),
                ],
                request_body=None,
                responses={
                    "200": ExtractedResponse(
                        status_code="200",
                        description="A single pet",
                        content_type="application/json",
                        schema_ref="Pet",
                    ),
                    "404": ExtractedResponse(
                        status_code="404",
                        description="Pet not found",
                        content_type=None,
                        schema_ref=None,
                    ),
                },
                deprecated=False,
            ),
            ExtractedEndpoint(
                path="/pets/{petId}",
                method="delete",
                summary="Delete a pet",
                description="Remove a pet from the store",
                operation_id="deletePet",
                tags=["pets"],
                parameters=[
                    ExtractedParameter(
                        name="petId",
                        location="path",
                        required=True,
                        schema_type="integer",
                        description="The ID of the pet to delete",
                    ),
                ],
                request_body=None,
                responses={
                    "204": ExtractedResponse(
                        status_code="204",
                        description="Pet deleted successfully",
                        content_type=None,
                        schema_ref=None,
                    ),
                    "404": ExtractedResponse(
                        status_code="404",
                        description="Pet not found",
                        content_type=None,
                        schema_ref=None,
                    ),
                },
                deprecated=False,
            ),
            ExtractedEndpoint(
                path="/users",
                method="get",
                summary="List all users",
                description=None,
                operation_id="listUsers",
                tags=["users"],
                parameters=[],
                request_body=None,
                responses={
                    "200": ExtractedResponse(
                        status_code="200",
                        description="A list of users",
                        content_type="application/json",
                        schema_ref="User",
                    ),
                },
                deprecated=False,
            ),
            ExtractedEndpoint(
                path="/users/{userId}",
                method="get",
                summary="Get a user by ID",
                description=None,
                operation_id="getUserById",
                tags=["users"],
                parameters=[
                    ExtractedParameter(
                        name="userId",
                        location="path",
                        required=True,
                        schema_type="integer",
                        description=None,
                    ),
                ],
                request_body=None,
                responses={
                    "200": ExtractedResponse(
                        status_code="200",
                        description="A single user",
                        content_type="application/json",
                        schema_ref="User",
                    ),
                    "404": ExtractedResponse(
                        status_code="404",
                        description="User not found",
                        content_type=None,
                        schema_ref=None,
                    ),
                },
                deprecated=False,
            ),
        ],
        schemas=[
            ExtractedSchema(
                name="Pet",
                type="object",
                description=None,
                properties=[
                    ExtractedProperty(name="id", type="integer", required=True, description="Unique identifier"),
                    ExtractedProperty(name="name", type="string", required=True, description="Name of the pet"),
                    ExtractedProperty(name="tag", type="string", required=False, description="Optional tag"),
                ],
                required=["id", "name"],
            ),
            ExtractedSchema(
                name="NewPet",
                type="object",
                description=None,
                properties=[
                    ExtractedProperty(name="name", type="string", required=True, description="Name of the pet"),
                    ExtractedProperty(name="tag", type="string", required=False, description="Optional tag"),
                ],
                required=["name"],
            ),
            ExtractedSchema(
                name="User",
                type="object",
                description=None,
                properties=[
                    ExtractedProperty(name="id", type="integer", required=True, description="Unique identifier"),
                    ExtractedProperty(name="username", type="string", required=True, description="Username"),
                    ExtractedProperty(name="email", type="string", required=False, description="Email address"),
                ],
                required=["id", "username"],
            ),
        ],
        security_schemes={
            "ApiKeyAuth": SecurityScheme(type="apiKey", scheme=None, name="X-API-Key", in_="header"),
            "BearerAuth": SecurityScheme(type="http", scheme="bearer", name=None, in_=None),
        },
        endpoint_count=6,
    )


@pytest.fixture
def sample_generate_request() -> OpenApiGenerateRequest:
    """Returns a sample generate request using petstore YAML."""
    return OpenApiGenerateRequest(
        spec=load_fixture("petstore.yaml"),
        spec_format="yaml",
        title="Pet Store Tests",
        context="Using pytest-asyncio for async tests",
    )


# ── Mock AI provider ──────────────────────────────────────────────


@pytest.fixture
def mock_ai_response() -> AIResponse:
    """Returns a mock AI response with generated test files."""
    content = json.dumps({
        "version": 1,
        "files": [
            {
                "filename": "test_pets.py",
                "content": (
                    "import pytest\nimport httpx\n\n"
                    "@pytest.mark.asyncio\nasync def test_list_pets_happy_path(\n"
                    "    client: httpx.AsyncClient,\n"
                    "    auth_headers: dict,\n"
                    ') -> None:\n    """GET /pets should return a list of pets."""\n'
                    '    response = await client.get("/pets", headers=auth_headers)\n'
                    "    assert response.status_code == 200\n"
                ),
            },
            {
                "filename": "test_users.py",
                "content": (
                    "import pytest\nimport httpx\n\n"
                    "@pytest.mark.asyncio\nasync def test_list_users_happy_path(\n"
                    "    client: httpx.AsyncClient,\n"
                    "    auth_headers: dict,\n"
                    ') -> None:\n    """GET /users should return a list of users."""\n'
                    '    response = await client.get("/users", headers=auth_headers)\n'
                    "    assert response.status_code == 200\n"
                ),
            },
        ],
    })
    return AIResponse(
        content=content,
        parsed=None,
        provider=ProviderMetadata(provider_name="test-provider", model="test-model", latency_ms=100),
        usage=UsageMetadata(prompt_tokens=500, completion_tokens=300, total_tokens=800),
    )


@pytest.fixture
def mock_provider_response(mock_ai_response):
    """Factory fixture that creates a mock provider with a given response."""

    def _create(response: AIResponse | None = None) -> MagicMock:
        provider = MagicMock()
        provider.name = "test-provider"

        async def generate(_request: AIRequest) -> AIResponse:
            return response or mock_ai_response

        provider.generate = AsyncMock(side_effect=generate)
        return provider

    return _create


@pytest.fixture
def mock_registry(mock_provider_response):
    """Returns a mock ProviderRegistry with the test provider registered."""

    def _create(provider=None):
        registry = MagicMock(spec=ProviderRegistry)
        registry.get.return_value = provider or mock_provider_response()
        return registry

    return _create


@pytest.fixture
def mock_prompt_manager():
    """Returns a mock PromptManager that returns a fixed prompt template."""
    pm = MagicMock(spec=PromptManager)

    def mock_load(analysis_type: str, context: dict[str, Any], version: str = "v1") -> PromptTemplate:
        from app.ai.prompt_manager import PromptTemplate, TemplateMetadata
        return PromptTemplate(
            system_prompt="You are a test generation AI. Generate tests for the given API endpoints.",
            user_message="Generate tests for the Pet Store API.",
            metadata=TemplateMetadata(
                analysis_type=analysis_type,
                version=version,
                template_path=Path(f"analysis/{analysis_type}/{version}"),
            ),
        )

    pm.load.side_effect = mock_load
    return pm
