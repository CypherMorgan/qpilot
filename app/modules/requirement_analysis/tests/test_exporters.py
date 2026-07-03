"""Tests for Requirement Analysis exporters."""

from __future__ import annotations

import json

import pytest

from app.modules.requirement_analysis.exporters import (
    JsonExporter,
    MarkdownExporter,
    get_exporter,
)
from app.modules.requirement_analysis.models import (
    PriorityAssessment,
    PriorityLevel,
    RequirementAnalysisResult,
)


class TestMarkdownExporter:
    """Tests for the Markdown exporter."""

    def test_export_returns_string(self, sample_analysis_result):
        """Export should return a non-empty string."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_export_contains_section_headers(self, sample_analysis_result):
        """The output should have all expected section headings."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert "# Requirement Analysis Report" in output
        assert "## Functional Test Cases" in output
        assert "## Negative Test Cases" in output
        assert "## Boundary Tests" in output
        assert "## Edge Cases" in output
        assert "## Assumptions" in output
        assert "## Risks" in output
        assert "## Missing Requirements" in output
        assert "## Suggested Questions" in output
        assert "## Automation Candidates" in output
        assert "## Priority Assessment" in output

    def test_export_contains_test_case_ids(self, sample_analysis_result):
        """Test case IDs should appear in the output."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert "TC-FUNC-001" in output
        assert "TC-FUNC-002" in output
        assert "TC-NEG-001" in output

    def test_export_contains_metadata(self, sample_analysis_result):
        """Input summary and timestamp should be in the output."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert sample_analysis_result.input_summary in output

    def test_export_empty_sections(self):
        """Empty sections should show a placeholder message."""
        result = RequirementAnalysisResult(
            input_summary="Empty test.",
            functional_tests=[],
            negative_tests=[],
            boundary_tests=[],
            edge_cases=[],
            assumptions=[],
            risks=[],
            missing_requirements=[],
            suggested_questions=[],
            automation_candidates=[],
            priority_assessment=PriorityAssessment(
                overall_priority=PriorityLevel.LOW,
                critical_path_items=[],
                quick_wins=[],
                reasoning="Empty test.",
            ),
        )
        exporter = MarkdownExporter()
        output = exporter.export(result)
        assert "_No functional test cases identified._" in output
        assert "_No negative test cases identified._" in output
        assert "_No automation candidates identified._" in output


class TestJsonExporter:
    """Tests for the JSON exporter."""

    def test_export_valid_json(self, sample_analysis_result):
        """Export should produce valid JSON."""
        exporter = JsonExporter()
        output = exporter.export(sample_analysis_result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_export_roundtrip(self, sample_analysis_result):
        """JSON output should roundtrip back to a RequirementAnalysisResult."""
        exporter = JsonExporter()
        output = exporter.export(sample_analysis_result)
        parsed = json.loads(output)
        restored = RequirementAnalysisResult.model_validate(parsed)
        assert restored.input_summary == sample_analysis_result.input_summary

    def test_export_pretty_printing(self, sample_analysis_result):
        """Output should be pretty-printed with indentation."""
        exporter = JsonExporter()
        output = exporter.export(sample_analysis_result)
        lines = output.split("\n")
        # Pretty-printed JSON has multiple lines
        assert len(lines) > 10
        # Has indentation
        assert "  " in output


class TestGetExporter:
    """Tests for the get_exporter factory."""

    def test_get_markdown_exporter(self):
        """Should return a MarkdownExporter for 'markdown'."""
        exporter = get_exporter("markdown")
        from app.modules.requirement_analysis.exporters import MarkdownExporter
        assert isinstance(exporter, MarkdownExporter)

    def test_get_json_exporter(self):
        """Should return a JsonExporter for 'json'."""
        exporter = get_exporter("json")
        from app.modules.requirement_analysis.exporters import JsonExporter
        assert isinstance(exporter, JsonExporter)

    def test_case_insensitive(self):
        """Format name should be case-insensitive."""
        exporter = get_exporter("MARKDOWN")
        from app.modules.requirement_analysis.exporters import MarkdownExporter
        assert isinstance(exporter, MarkdownExporter)

    def test_unsupported_format_raises(self):
        """Unsupported format should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            get_exporter("pdf")
