"""Shared test fixtures for Failure Analysis module tests.

Sets test environment variables at module level (before app imports)
to ensure tests use an in-memory SQLite database and don't require
a running PostgreSQL instance.

Provides mock providers, mock prompt manager, and sample analysis
result data for use across service, router, and exporter tests.
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

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.prompt_manager import PromptTemplate, TemplateMetadata
from app.modules.failure_analysis.models import (
    AffectedComponent,
    FailureAnalysisResult,
    FailureCategory,
    FailureSeverity,
    FixPriority,
    RootCause,
    StackFrame,
    SuggestedFix,
    TestFailure,
)


@pytest.fixture
def sample_analysis_result() -> FailureAnalysisResult:
    """A complete, valid FailureAnalysisResult for testing.

    This fixture provides realistic sample data that can be used
    across exporter, parser, and presentation tests.
    """
    return FailureAnalysisResult(
        input_summary="CI test run failure in the user authentication module. 3 tests failed with assertion errors in the login flow.",
        analysis_timestamp=datetime(2026, 7, 1, 12, 0, 0),
        summary="The authentication test suite failed due to a recent refactor of the session management layer. The session token validation logic was changed, causing existing login tests to fail because they expect the old token format.",
        root_causes=[
            RootCause(
                id="RC-001",
                title="Session token validation mismatch after refactor",
                description="The session management refactor changed the token structure from JWT to opaque tokens, but the test helpers still validate against the old JWT format.",
                category=FailureCategory.ASSERTION_ERROR,
                severity=FailureSeverity.HIGH,
                failing_file="tests/integration/test_auth.py",
                failing_line=42,
                stack_trace=[
                    StackFrame(
                        file="tests/integration/test_auth.py",
                        line=42,
                        function="test_login_success",
                        code="assert response.json()['token'].startswith('eyJ')",
                    ),
                    StackFrame(
                        file="app/auth/session.py",
                        line=128,
                        function="create_session",
                        code="return OpaqueToken(user_id, expiry)",
                    ),
                ],
                error_message="AssertionError: assert False\n +  where False = <built-in method startswith of str object at 0x...>('eyJ')",
            ),
            RootCause(
                id="RC-002",
                title="Missing session scope in test fixture",
                description="The test fixture for authenticated requests was not updated to request the new 'session:write' scope required by the refactored session service.",
                category=FailureCategory.CONFIGURATION,
                severity=FailureSeverity.MEDIUM,
                failing_file="tests/conftest.py",
                failing_line=15,
                error_message="ScopeError: Required scope 'session:write' is missing",
            ),
        ],
        suggested_fixes=[
            SuggestedFix(
                id="FIX-001",
                root_cause_id="RC-001",
                description="Update test assertions to match the new opaque token format. Instead of checking for a JWT prefix, validate that the session ID is a valid UUID and that the token endpoint returns a 200 status.",
                priority=FixPriority.HIGH,
                effort_estimate="30 minutes",
                code_example='# Before:\nassert response.json()["token"].startswith("eyJ")\n\n# After:\nimport uuid\nsession = response.json()\nassert "session_id" in session\nuuid.UUID(session["session_id"])',
                related_files=["tests/integration/test_auth.py"],
            ),
            SuggestedFix(
                id="FIX-002",
                root_cause_id="RC-002",
                description="Add the 'session:write' scope to the authenticated test fixture in conftest.py.",
                priority=FixPriority.MEDIUM,
                effort_estimate="15 minutes",
                code_example="# Before:\nscopes=[\"session:read\"]\n\n# After:\nscopes=[\"session:read\", \"session:write\"]",
                related_files=["tests/conftest.py"],
            ),
        ],
        affected_components=[
            AffectedComponent(
                id="CMP-001",
                name="Authentication Service",
                impact="Login flow is broken. Users cannot authenticate with the new session layer.",
                related_root_causes=["RC-001"],
            ),
            AffectedComponent(
                id="CMP-002",
                name="Test Fixtures",
                impact="All authenticated test requests fail due to missing scopes.",
                related_root_causes=["RC-002"],
            ),
        ],
        test_failures=[
            TestFailure(
                id="TF-001",
                test_name="tests/integration/test_auth.py::test_login_success",
                test_file="tests/integration/test_auth.py",
                error_message="AssertionError: assert False",
                duration_seconds=1.2,
                retry_count=0,
            ),
            TestFailure(
                id="TF-002",
                test_name="tests/integration/test_auth.py::test_login_invalid_credentials",
                test_file="tests/integration/test_auth.py",
                error_message="ScopeError: Required scope 'session:write' is missing",
                duration_seconds=0.8,
                retry_count=1,
            ),
            TestFailure(
                id="TF-003",
                test_name="tests/integration/test_auth.py::test_session_refresh",
                test_file="tests/integration/test_auth.py",
                error_message="AttributeError: 'OpaqueToken' object has no attribute 'decode'",
                duration_seconds=0.5,
                retry_count=0,
            ),
        ],
        environment_details=[
            "Python 3.12",
            "pytest 8.0",
            "CI runner: GitHub Actions ubuntu-latest",
            "Commit: a1b2c3d (feature/session-refactor)",
        ],
        recommendations=[
            "Run the full test suite to check for additional failures before merging.",
            "Add a migration guide for the new session token format to the team wiki.",
            "Consider adding a compatibility shim during the transition period.",
        ],
        related_tests=[
            "tests/integration/test_session_expiry.py",
            "tests/unit/test_token_validator.py",
            "tests/integration/test_logout.py",
        ],
    )


@pytest.fixture
def mock_provider_response() -> AIResponse:
    """A mock AIResponse as if returned by an AI provider."""
    return AIResponse(
        content="""{
            "input_summary": "Test failure.",
            "summary": "A test summary.",
            "root_causes": [],
            "suggested_fixes": [],
            "affected_components": [],
            "test_failures": [],
            "environment_details": [],
            "recommendations": [],
            "related_tests": []
        }""",
        parsed=None,
        usage=TokenUsage(prompt_tokens=50, completion_tokens=100, total_tokens=150),
        provider=ProviderMetadata(
            provider_name="mock",
            model="mock-model-v1",
            latency_ms=42,
        ),
    )


@pytest.fixture
def mock_prompt_manager():
    """A PromptManager with ``load()`` returning a canned PromptTemplate."""
    mgr = MagicMock()
    mgr.load.return_value = PromptTemplate(
        system_prompt="System instructions.",
        user_message="User content.",
        metadata=TemplateMetadata(
            analysis_type="failure-analysis",
            version="v1",
            template_path=MagicMock(),
        ),
    )
    mgr.clear_cache = MagicMock()
    return mgr


@pytest.fixture
def mock_provider():
    """A mock AI provider that returns canned responses."""
    provider = MagicMock()
    provider.name = "mock"

    async def generate(request: AIRequest) -> AIResponse:
        return AIResponse(
            content='{"input_summary":"Test.","summary":"Summary.","root_causes":[],"suggested_fixes":[],"affected_components":[],"test_failures":[],"environment_details":[],"recommendations":[],"related_tests":[]}',
            parsed=None,
            usage=TokenUsage(prompt_tokens=50, completion_tokens=100, total_tokens=150),
            provider=ProviderMetadata(
                provider_name="mock",
                model="mock-model",
                latency_ms=42,
            ),
        )

    provider.generate = generate
    return provider


@pytest.fixture
def mock_registry(mock_provider):
    """A ProviderRegistry pre-populated with the mock provider."""
    from app.ai.registry import ProviderRegistry

    reg = ProviderRegistry()
    reg.register("mock", mock_provider)
    return reg


@pytest.fixture
def mock_repository():
    """A mock repository that bypasses the database."""
    repo = AsyncMock()
    repo.create.return_value.id = uuid4()
    repo.get.return_value = None
    return repo
