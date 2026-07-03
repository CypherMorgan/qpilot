"""Tests for Requirement Analysis Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.requirement_analysis.models import (
    AnalysisRequest,
    BoundaryTestCase,
    EdgeCase,
    FunctionalTestCase,
    InputSourceType,
    PriorityLevel,
    RequirementAnalysisResult,
    Risk,
    RiskSeverity,
)


class TestAnalysisRequest:
    """Tests for the AnalysisRequest input schema."""

    def test_valid_request(self):
        """A valid AnalysisRequest should be accepted."""
        req = AnalysisRequest(content="The system shall allow users to log in.")
        assert req.content == "The system shall allow users to log in."
        assert req.source_type == InputSourceType.PLAIN_TEXT
        assert req.output_format == "json"
        assert req.title is None

    def test_empty_content_raises(self):
        """Content must not be empty."""
        with pytest.raises(ValidationError):
            AnalysisRequest(content="")

    def test_markdown_source_type(self):
        """Markdown source type should be accepted."""
        req = AnalysisRequest(
            content="# Requirements\n- Login\n- Logout",
            source_type=InputSourceType.MARKDOWN,
        )
        assert req.source_type == InputSourceType.MARKDOWN

    def test_acceptance_criteria_source_type(self):
        """Acceptance criteria source type should be accepted."""
        req = AnalysisRequest(
            content="Given a registered user\nWhen they log in\nThen...",
            source_type=InputSourceType.ACCEPTANCE_CRITERIA,
        )
        assert req.source_type == InputSourceType.ACCEPTANCE_CRITERIA

    def test_optional_fields(self):
        """Optional fields should be settable."""
        req = AnalysisRequest(
            content="Test content.",
            title="Login Analysis",
            context="Tech stack: React, Node.js",
            output_format="both",
        )
        assert req.title == "Login Analysis"
        assert req.context == "Tech stack: React, Node.js"
        assert req.output_format == "both"


class TestFunctionalTestCase:
    """Tests for FunctionalTestCase model."""

    def test_minimal_test_case(self):
        """A test case requires only id, title, description, steps, and expected_result."""
        tc = FunctionalTestCase(
            id="TC-FUNC-001",
            title="Successful login",
            description="Verify login works",
            steps=["Enter email", "Enter password", "Click login"],
            expected_result="User is logged in",
        )
        assert tc.id == "TC-FUNC-001"
        assert tc.priority == PriorityLevel.MEDIUM
        assert tc.preconditions == []

    def test_empty_steps_raises(self):
        """Steps must have at least one item."""
        with pytest.raises(ValidationError):
            FunctionalTestCase(
                id="TC-FUNC-001",
                title="Test",
                description="Desc",
                steps=[],
                expected_result="Result",
            )

    def test_full_test_case(self):
        """All fields should be settable."""
        tc = FunctionalTestCase(
            id="TC-FUNC-001",
            title="Test",
            description="Desc",
            preconditions=["User exists"],
            steps=["Step 1"],
            expected_result="Result",
            priority=PriorityLevel.CRITICAL,
            tags=["security", "auth"],
        )
        assert tc.priority == PriorityLevel.CRITICAL
        assert "security" in tc.tags

    def test_priority_enum_values(self):
        """All priority levels should be valid."""
        for level in PriorityLevel:
            tc = FunctionalTestCase(
                id="TC-001",
                title="Test",
                description="Desc",
                steps=["Step"],
                expected_result="Result",
                priority=level,
            )
            assert tc.priority == level


class TestBoundaryTestCase:
    """Tests for BoundaryTestCase model."""

    def test_boundary_value_required(self):
        """BoundaryTestCase requires a boundary_value."""
        tc = BoundaryTestCase(
            id="TC-BND-001",
            title="Max length",
            description="Test 255 chars",
            steps=["Enter 255 chars"],
            expected_result="Accepted",
            boundary_value="255 characters",
        )
        assert tc.boundary_value == "255 characters"


class TestEdgeCase:
    """Tests for EdgeCase model."""

    def test_minimal_edge_case(self):
        """An edge case requires id, title, description, and impact."""
        ec = EdgeCase(
            id="EC-001",
            title="Concurrent sessions",
            description="Multiple logins from different devices",
            impact="Potential session conflicts",
        )
        assert ec.id == "EC-001"
        assert ec.recommendation is None

    def test_full_edge_case(self):
        """All fields should be settable."""
        ec = EdgeCase(
            id="EC-001",
            title="Test",
            description="Desc",
            impact="Impact",
            recommendation="Recommendation",
        )
        assert ec.recommendation == "Recommendation"


class TestRisk:
    """Tests for Risk model."""

    def test_minimal_risk(self):
        """A risk requires id, description, severity, and likelihood."""
        r = Risk(
            id="RSK-001",
            description="Brute force attack",
            severity=RiskSeverity.HIGH,
            likelihood="medium",
        )
        assert r.mitigation is None

    def test_full_risk(self):
        """All fields should be settable."""
        r = Risk(
            id="RSK-001",
            description="Attack",
            severity=RiskSeverity.CRITICAL,
            likelihood="high",
            mitigation="Rate limit",
        )
        assert r.mitigation == "Rate limit"


class TestRequirementAnalysisResult:
    """Tests for the top-level RequirementAnalysisResult model."""

    def test_minimal_result(self, sample_analysis_result):
        """A complete valid result should have all sections."""
        result = sample_analysis_result
        assert len(result.functional_tests) == 2
        assert len(result.negative_tests) == 1
        assert len(result.boundary_tests) == 1
        assert len(result.edge_cases) == 1
        assert len(result.assumptions) == 2
        assert len(result.risks) == 1
        assert len(result.missing_requirements) == 1
        assert len(result.suggested_questions) == 2
        assert len(result.automation_candidates) == 1
        assert result.priority_assessment.overall_priority == PriorityLevel.HIGH

    def test_model_dump_roundtrip(self, sample_analysis_result):
        """The result should survive a model_dump -> model_validate round trip."""
        dumped = sample_analysis_result.model_dump(mode="json")
        restored = RequirementAnalysisResult.model_validate(dumped)
        assert restored.input_summary == sample_analysis_result.input_summary
        assert len(restored.functional_tests) == len(sample_analysis_result.functional_tests)
        assert restored.priority_assessment.overall_priority == PriorityLevel.HIGH


class TestInputSourceType:
    """Tests for the InputSourceType enum."""

    def test_values(self):
        assert InputSourceType.PLAIN_TEXT.value == "plain_text"
        assert InputSourceType.MARKDOWN.value == "markdown"
        assert InputSourceType.ACCEPTANCE_CRITERIA.value == "acceptance_criteria"


class TestPriorityLevel:
    """Tests for the PriorityLevel enum."""

    def test_values(self):
        assert PriorityLevel.CRITICAL.value == "critical"
        assert PriorityLevel.HIGH.value == "high"
        assert PriorityLevel.MEDIUM.value == "medium"
        assert PriorityLevel.LOW.value == "low"
