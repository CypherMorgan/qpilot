"""Tests for Failure Analysis Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.failure_analysis.models import (
    AffectedComponent,
    AnalysisRequest,
    FailureAnalysisResult,
    FailureCategory,
    FailureSeverity,
    FixPriority,
    InputSourceType,
    RootCause,
    StackFrame,
    SuggestedFix,
    TestFailure,
)


class TestAnalysisRequest:
    """Tests for the AnalysisRequest input schema."""

    def test_valid_request(self):
        """A valid AnalysisRequest should be accepted."""
        req = AnalysisRequest(content="AssertionError: expected 200, got 500")
        assert req.content == "AssertionError: expected 200, got 500"
        assert req.source_type == InputSourceType.PLAIN_TEXT
        assert req.output_format == "json"
        assert req.title is None

    def test_empty_content_raises(self):
        """Content must not be empty."""
        with pytest.raises(ValidationError):
            AnalysisRequest(content="")

    def test_ci_log_source_type(self):
        """CI log source type should be accepted."""
        req = AnalysisRequest(
            content="[FAIL] test_login failed",
            source_type=InputSourceType.CI_LOG,
        )
        assert req.source_type == InputSourceType.CI_LOG

    def test_stack_trace_source_type(self):
        """Stack trace source type should be accepted."""
        req = AnalysisRequest(
            content="Traceback (most recent call last):",
            source_type=InputSourceType.STACK_TRACE,
        )
        assert req.source_type == InputSourceType.STACK_TRACE

    def test_optional_fields(self):
        """Optional fields should be settable."""
        req = AnalysisRequest(
            content="Test content.",
            title="Login Failure Analysis",
            context="Language: Python, Framework: pytest",
            output_format="both",
        )
        assert req.title == "Login Failure Analysis"
        assert req.context == "Language: Python, Framework: pytest"
        assert req.output_format == "both"


class TestStackFrame:
    """Tests for StackFrame model."""

    def test_minimal_stack_frame(self):
        """A stack frame requires only file and line."""
        frame = StackFrame(file="test_auth.py", line=42)
        assert frame.file == "test_auth.py"
        assert frame.line == 42
        assert frame.function == ""

    def test_full_stack_frame(self):
        """All fields should be settable."""
        frame = StackFrame(
            file="test_auth.py",
            line=42,
            function="test_login_success",
            code="assert result == expected",
        )
        assert frame.function == "test_login_success"
        assert frame.code == "assert result == expected"


class TestRootCause:
    """Tests for RootCause model."""

    def test_minimal_root_cause(self):
        """A root cause requires id, title, description, category, severity."""
        rc = RootCause(
            id="RC-001",
            title="Assertion mismatch",
            description="The expected value does not match actual output.",
            category=FailureCategory.ASSERTION_ERROR,
            severity=FailureSeverity.HIGH,
        )
        assert rc.id == "RC-001"
        assert rc.category == FailureCategory.ASSERTION_ERROR
        assert rc.failing_file is None

    def test_full_root_cause(self):
        """All fields should be settable."""
        rc = RootCause(
            id="RC-001",
            title="Test",
            description="Desc",
            category=FailureCategory.ENVIRONMENT,
            severity=FailureSeverity.CRITICAL,
            failing_file="test.py",
            failing_line=10,
            stack_trace=[StackFrame(file="test.py", line=10)],
            error_message="Error!",
        )
        assert rc.failing_file == "test.py"
        assert rc.failing_line == 10
        assert rc.error_message == "Error!"
        assert len(rc.stack_trace) == 1

    def test_category_enum_values(self):
        """All failure category values should be valid."""
        for cat in FailureCategory:
            rc = RootCause(
                id="RC-001",
                title="Test",
                description="Desc",
                category=cat,
                severity=FailureSeverity.LOW,
            )
            assert rc.category == cat


class TestSuggestedFix:
    """Tests for SuggestedFix model."""

    def test_minimal_fix(self):
        """A suggested fix requires id, root_cause_id, description, priority."""
        fix = SuggestedFix(
            id="FIX-001",
            root_cause_id="RC-001",
            description="Update the test assertion.",
            priority=FixPriority.HIGH,
        )
        assert fix.id == "FIX-001"
        assert fix.code_example is None

    def test_full_fix(self):
        """All fields should be settable."""
        fix = SuggestedFix(
            id="FIX-001",
            root_cause_id="RC-001",
            description="Fix",
            priority=FixPriority.CRITICAL,
            effort_estimate="1 hour",
            code_example="assert True",
            related_files=["test.py"],
        )
        assert fix.code_example == "assert True"
        assert "test.py" in fix.related_files


class TestAffectedComponent:
    """Tests for AffectedComponent model."""

    def test_minimal_component(self):
        """An affected component requires id, name, impact."""
        cmp = AffectedComponent(
            id="CMP-001",
            name="Auth Service",
            impact="Login flow is broken.",
        )
        assert cmp.id == "CMP-001"
        assert cmp.related_root_causes == []


class TestTestFailure:
    """Tests for TestFailure model."""

    def test_minimal_test_failure(self):
        """A test failure requires id and test_name."""
        tf = TestFailure(id="TF-001", test_name="test_login")
        assert tf.test_file == ""
        assert tf.retry_count == 0
        assert tf.duration_seconds is None


class TestFailureAnalysisResult:
    """Tests for the top-level FailureAnalysisResult model."""

    def test_minimal_result(self, sample_analysis_result):
        """A complete valid result should have all sections."""
        result = sample_analysis_result
        assert len(result.root_causes) == 2
        assert len(result.suggested_fixes) == 2
        assert len(result.affected_components) == 2
        assert len(result.test_failures) == 3
        assert len(result.environment_details) == 4
        assert len(result.recommendations) == 3
        assert len(result.related_tests) == 3

    def test_model_dump_roundtrip(self, sample_analysis_result):
        """The result should survive a model_dump -> model_validate round trip."""
        dumped = sample_analysis_result.model_dump(mode="json")
        restored = FailureAnalysisResult.model_validate(dumped)
        assert restored.input_summary == sample_analysis_result.input_summary
        assert len(restored.root_causes) == len(sample_analysis_result.root_causes)
        assert len(restored.suggested_fixes) == len(sample_analysis_result.suggested_fixes)

    def test_empty_sections(self):
        """Empty lists should be accepted."""
        result = FailureAnalysisResult(
            input_summary="Test.",
            summary="Test summary.",
            root_causes=[],
            suggested_fixes=[],
            affected_components=[],
            test_failures=[],
            environment_details=[],
            recommendations=[],
            related_tests=[],
        )
        assert len(result.root_causes) == 0
        assert len(result.test_failures) == 0


class TestInputSourceType:
    """Tests for the InputSourceType enum."""

    def test_values(self):
        assert InputSourceType.PLAIN_TEXT.value == "plain_text"
        assert InputSourceType.MARKDOWN.value == "markdown"
        assert InputSourceType.CI_LOG.value == "ci_log"
        assert InputSourceType.STACK_TRACE.value == "stack_trace"


class TestFailureSeverity:
    """Tests for the FailureSeverity enum."""

    def test_values(self):
        assert FailureSeverity.CRITICAL.value == "critical"
        assert FailureSeverity.HIGH.value == "high"
        assert FailureSeverity.MEDIUM.value == "medium"
        assert FailureSeverity.LOW.value == "low"


class TestFailureCategory:
    """Tests for the FailureCategory enum."""

    def test_values(self):
        assert FailureCategory.ASSERTION_ERROR.value == "assertion_error"
        assert FailureCategory.TIMEOUT.value == "timeout"
        assert FailureCategory.ENVIRONMENT.value == "environment"
        assert FailureCategory.UNKNOWN.value == "unknown"
