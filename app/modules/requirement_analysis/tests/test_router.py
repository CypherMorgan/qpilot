"""Tests for Requirement Analysis API endpoints.

Uses the test app with mocked state to verify routing, request
validation, and response structure.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.ai.models import AIResponse, ProviderMetadata, TokenUsage
from app.ai.prompt_manager import PromptTemplate, TemplateMetadata
from app.main import create_app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """App fixture: runs lifespan, overrides provider dependencies.

    Uses the standard LifespanManager pattern (same as conftest.py)
    then patches the provider_registry and prompt_manager with mocks.
    """
    app = create_app()

    async with LifespanManager(app):
        # Ensure the test database has the required schema
        db_manager = getattr(app.state, "db_manager", None)
        if db_manager is not None:
            await db_manager.create_all()

        # Override the provider registry with a mock
        mock_provider = AsyncMock()
        mock_provider.name = "mock"

        async def mock_generate(request):
            return AIResponse(
                content='{"input_summary":"Test.","functional_tests":[],"negative_tests":[],"boundary_tests":[],"edge_cases":[],"assumptions":[],"risks":[],"missing_requirements":[],"suggested_questions":[],"automation_candidates":[],"priority_assessment":{"overall_priority":"medium","critical_path_items":[],"quick_wins":[],"reasoning":"Test."}}',
                parsed=None,
                usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                provider=ProviderMetadata(provider_name="mock", model="mock-model", latency_ms=5),
            )

        mock_provider.generate = mock_generate

        mock_registry = MagicMock()
        mock_registry.get = MagicMock(return_value=mock_provider)

        mock_pm = MagicMock()
        mock_pm.load.return_value = PromptTemplate(
            system_prompt="System.",
            user_message="User.",
            metadata=TemplateMetadata(
                analysis_type="requirement-analysis",
                version="v1",
                template_path=MagicMock(),
            ),
        )

        app.state.provider_registry = mock_registry
        app.state.prompt_manager = mock_pm
        app.state.config.ai.provider = "mock"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


class TestAnalyzeEndpoint:
    """Tests for POST /api/v1/requirements/analyze."""

    async def test_analyze_success(self, client):
        """Valid request should return 200 with analysis result."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={"content": "The system shall allow users to log in."},
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "session_id" in body["data"]
        assert body["data"]["status"] == "completed"
        assert "result" in body["data"]

    async def test_analyze_empty_content(self, client):
        """Empty content should return 422 validation error."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={"content": ""},
        )
        assert response.status_code == 422

    async def test_analyze_missing_content(self, client):
        """Missing content field should return 422."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={},
        )
        assert response.status_code == 422

    async def test_analyze_with_title(self, client):
        """Request with title should be accepted."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={
                "content": "Login requirements.",
                "title": "Login Analysis",
                "source_type": "plain_text",
            },
        )
        assert response.status_code == 200

    async def test_analyze_with_markdown(self, client):
        """Markdown source type should be accepted."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={
                "content": "# Requirements\n- Login",
                "source_type": "markdown",
            },
        )
        assert response.status_code == 200

    async def test_analyze_invalid_source_type(self, client):
        """Invalid source type should return 422."""
        response = await client.post(
            "/api/v1/requirements/analyze",
            json={
                "content": "Test.",
                "source_type": "invalid",
            },
        )
        assert response.status_code == 422


class TestGetSessionEndpoint:
    """Tests for GET /api/v1/requirements/sessions/{id}."""

    async def test_get_nonexistent_session(self, client):
        """Non-existent session should return 404."""
        response = await client.get(
            f"/api/v1/requirements/sessions/{UUID('00000000-0000-0000-0000-000000000099')}",
        )
        assert response.status_code == 404


class TestListSessionsEndpoint:
    """Tests for GET /api/v1/requirements/sessions."""

    async def test_list_sessions(self, client):
        """Listing sessions should return 200 with pagination."""
        response = await client.get("/api/v1/requirements/sessions")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert "pagination" in body["meta"]

    async def test_list_sessions_pagination(self, client):
        """Pagination params should be accepted."""
        response = await client.get(
            "/api/v1/requirements/sessions?page=1&page_size=10",
        )
        assert response.status_code == 200
