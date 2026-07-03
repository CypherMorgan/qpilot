"""Shared test fixtures and configuration.

Every test file imports from here. Fixtures are discovered automatically
by pytest.

Environment variables are set at module level (before app imports) to
satisfy AppConfig validation during application creation.
"""

from __future__ import annotations

import os

# ═══════════════════════════════════════════════════════════════════════
# Set test environment BEFORE any app imports
# The module-level `app = create_app()` in app/main.py runs at import
# time, so env vars must be present before `from app.main import
# create_app`.
# ═══════════════════════════════════════════════════════════════════════
os.environ.setdefault("AI__OPENROUTER_API_KEY", "test-key-for-unit-tests")
os.environ.setdefault("AI__PROVIDER", "openrouter")

# Use in-memory SQLite for all tests so we don't need PostgreSQL.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")

from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.registry import ProviderRegistry
from app.infrastructure.database import AsyncSession, DatabaseManager
from app.infrastructure.models import (
    AnalysisSession,  # noqa: F401 — registers model on Base.metadata
)
from app.main import create_app

# ── Database fixtures ───────────────────────────────────────────


@pytest.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """Return a ``DatabaseManager`` backed by in-memory SQLite.

    Creates all tables before the test and drops them on teardown.
    Use this for repository / integration tests that need a real
    database but no HTTP server.
    """
    manager = DatabaseManager(
        database_url="sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    await manager.create_all()
    yield manager
    await manager.drop_all()
    await manager.close()


@pytest.fixture
async def db_session(
    db_manager: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Return a fresh ``AsyncSession`` backed by the test database.

    The session is scoped to a single test function.  The transaction
    is rolled back after the test, leaving no side effects.
    """
    async with db_manager.session() as session:
        yield session


# ── HTTP client fixtures ────────────────────────────────────────


@pytest.fixture
def app() -> FastAPI:
    """Return a fresh application instance for testing.

    Each test function gets a new app to prevent state leakage.
    """
    return create_app()


@pytest.fixture
async def client(
    app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """Return an async HTTP client backed by the app (no server needed).

    Automatically manages the application lifespan via LifespanManager.
    """
    async with LifespanManager(app):
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client


# ── AI test fixtures ──────────────────────────────────────────


class MockResult(BaseModel):
    """Simple model for testing response parsing."""

    result: str


class MockAIProvider:
    """A provider that returns predictable responses without real API calls."""

    @property
    def name(self) -> str:
        return "mock"

    async def generate(self, request: AIRequest) -> AIResponse:
        parsed = None
        content = '{"result": "mocked"}'
        if request.response_model:
            parsed = request.response_model.model_validate_json(content)
        return AIResponse(
            content=content,
            parsed=parsed,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            provider=ProviderMetadata(
                provider_name="mock",
                model="mock-model",
                latency_ms=5,
            ),
        )


@pytest.fixture
def mock_provider() -> MockAIProvider:
    """A provider stub that returns canned responses."""
    return MockAIProvider()


@pytest.fixture
def registry(mock_provider: MockAIProvider) -> ProviderRegistry:
    """A registry pre-populated with a mock provider."""
    reg = ProviderRegistry()
    reg.register("mock", mock_provider)
    return reg


@pytest.fixture
def ai_request() -> AIRequest:
    """A basic AIRequest for use in provider tests."""
    return AIRequest(
        system_prompt="You are a helpful assistant.",
        user_message="Generate a test result.",
        response_model=MockResult,
        temperature=0.0,
    )
