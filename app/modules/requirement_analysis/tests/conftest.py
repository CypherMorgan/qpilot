"""Shared test fixtures for Requirement Analysis module tests.

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
from app.modules.requirement_analysis.models import (
    AutomationCandidate,
    AutomationFeasibility,
    BoundaryTestCase,
    EdgeCase,
    FunctionalTestCase,
    MissingRequirement,
    NegativeTestCase,
    PriorityAssessment,
    PriorityLevel,
    RequirementAnalysisResult,
    Risk,
    RiskSeverity,
)


@pytest.fixture
def sample_analysis_result() -> RequirementAnalysisResult:
    """A complete, valid RequirementAnalysisResult for testing.

    This fixture provides realistic sample data that can be used
    across exporter, parser, and presentation tests.
    """
    return RequirementAnalysisResult(
        input_summary="User authentication requirements covering email/password login with session management.",
        analysis_timestamp=datetime(2026, 7, 1, 12, 0, 0),
        functional_tests=[
            FunctionalTestCase(
                id="TC-FUNC-001",
                title="Successful login with valid credentials",
                description="Verify that a user can log in with a valid email and password.",
                preconditions=["User account exists and is active."],
                steps=[
                    "Navigate to the login page.",
                    "Enter a registered email address.",
                    "Enter the correct password.",
                    "Click the 'Login' button.",
                ],
                expected_result="User is redirected to the dashboard.",
                priority=PriorityLevel.HIGH,
                tags=["login", "happy-path"],
            ),
            FunctionalTestCase(
                id="TC-FUNC-002",
                title="Session token is issued on login",
                description="Verify that a valid session token is returned upon successful authentication.",
                preconditions=["User account exists and is active."],
                steps=[
                    "Log in with valid credentials.",
                    "Inspect the response headers and cookies.",
                ],
                expected_result="A session token (JWT) is returned in the response body and set as a secure, HTTP-only cookie.",
                priority=PriorityLevel.HIGH,
                tags=["login", "session", "security"],
            ),
        ],
        negative_tests=[
            NegativeTestCase(
                id="TC-NEG-001",
                title="Login with incorrect password",
                description="Verify login is rejected with wrong password.",
                preconditions=["User account exists."],
                steps=[
                    "Navigate to the login page.",
                    "Enter a registered email address.",
                    "Enter an incorrect password.",
                    "Click the 'Login' button.",
                ],
                expected_result="Login is rejected. Error message: 'Invalid email or password.' No session token is issued.",
                priority=PriorityLevel.HIGH,
                tags=["login", "negative", "authentication"],
            ),
        ],
        boundary_tests=[
            BoundaryTestCase(
                id="TC-BND-001",
                title="Maximum password length",
                description="Verify that a password at the maximum allowed length is accepted.",
                preconditions=["Maximum password length is defined (e.g., 128 characters)."],
                steps=[
                    "Navigate to registration page.",
                    "Enter a valid email.",
                    "Enter a password of 128 characters meeting complexity rules.",
                    "Submit the registration form.",
                ],
                expected_result="Registration succeeds. Account is created.",
                priority=PriorityLevel.MEDIUM,
                tags=["registration", "boundary"],
                boundary_value="128 characters",
            ),
        ],
        edge_cases=[
            EdgeCase(
                id="EC-001",
                title="Concurrent login from multiple devices",
                description="What happens when the same user logs in from two different browsers simultaneously?",
                impact="Both sessions should be valid. User may be confused if old sessions are invalidated without notice.",
                recommendation="Issue distinct session tokens per device. Display active sessions in account settings.",
            ),
        ],
        assumptions=[
            "Passwords are hashed using bcrypt or equivalent before storage.",
            "Session tokens expire after a configurable period (e.g., 24 hours).",
        ],
        risks=[
            Risk(
                id="RSK-001",
                description="Brute-force login attacks could compromise accounts.",
                severity=RiskSeverity.CRITICAL,
                likelihood="high",
                mitigation="Implement rate limiting on the login endpoint. Lock accounts after 5 failed attempts.",
            ),
        ],
        missing_requirements=[
            MissingRequirement(
                id="MR-001",
                topic="Password reset flow",
                description="The requirements specify login but do not describe how users can reset forgotten passwords.",
                importance=PriorityLevel.HIGH,
            ),
        ],
        suggested_questions=[
            "What is the session token expiry time?",
            "Should the system support multi-factor authentication (MFA)?",
        ],
        automation_candidates=[
            AutomationCandidate(
                id="AUTO-001",
                test_case_id="TC-FUNC-001",
                feasibility=AutomationFeasibility.EASY,
                effort_estimate="1-2 hours",
                value_reason="Core login flow should be tested on every deployment.",
            ),
        ],
        priority_assessment=PriorityAssessment(
            overall_priority=PriorityLevel.HIGH,
            critical_path_items=["TC-FUNC-001", "TC-NEG-001"],
            quick_wins=["TC-NEG-001"],
            reasoning="Login is the entry point to the product. Core flows must work reliably before launch.",
        ),
    )


@pytest.fixture
def mock_provider_response() -> AIResponse:
    """A mock AIResponse as if returned by an AI provider."""
    return AIResponse(
        content="""{
            "input_summary": "Test requirements.",
            "functional_tests": [],
            "negative_tests": [],
            "boundary_tests": [],
            "edge_cases": [],
            "assumptions": [],
            "risks": [],
            "missing_requirements": [],
            "suggested_questions": [],
            "automation_candidates": [],
            "priority_assessment": {
                "overall_priority": "medium",
                "critical_path_items": [],
                "quick_wins": [],
                "reasoning": "Test reason."
            }
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
            analysis_type="requirement-analysis",
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
            content='{"input_summary":"Test.","functional_tests":[],"negative_tests":[],"boundary_tests":[],"edge_cases":[],"assumptions":[],"risks":[],"missing_requirements":[],"suggested_questions":[],"automation_candidates":[],"priority_assessment":{"overall_priority":"medium","critical_path_items":[],"quick_wins":[],"reasoning":"Test."}}',
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
