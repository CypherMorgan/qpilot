"""Tests for Failure Analysis exporters."""

from __future__ import annotations

import json

import pytest

from app.modules.failure_analysis.exporters import (
    JsonExporter,
    MarkdownExporter,
    get_exporter,
)
from app.modules.failure_analysis.models import (
    FailureAnalysisResult,
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
        assert "# Automation Failure Analysis Report" in output
        assert "## Summary" in output
        assert "## Root Causes" in output
        assert "## Suggested Fixes" in output
        assert "## Affected Components" in output
        assert "## Test Failures" in output
        assert "## Environment Details" in output
        assert "## Recommendations" in output
        assert "## Related Tests" in output

    def test_export_contains_root_cause_ids(self, sample_analysis_result):
        """Root cause IDs should appear in the output."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert "RC-001" in output
        assert "RC-002" in output

    def test_export_contains_fix_ids(self, sample_analysis_result):
        """Fix IDs should appear in the output."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert "FIX-001" in output
        assert "FIX-002" in output

    def test_export_contains_metadata(self, sample_analysis_result):
        """Input summary and timestamp should be in the output."""
        exporter = MarkdownExporter()
        output = exporter.export(sample_analysis_result)
        assert sample_analysis_result.input_summary in output

    def test_export_empty_sections(self):
        """Empty sections should show a placeholder message."""
        result = FailureAnalysisResult(
            input_summary="Empty test.",
            summary="Empty summary.",
            root_causes=[],
            suggested_fixes=[],
            affected_components=[],
            test_failures=[],
            environment_details=[],
            recommendations=[],
            related_tests=[],
        )
        exporter = MarkdownExporter()
        output = exporter.export(result)
        assert "_No root causes identified._" in output
        assert "_No suggested fixes identified._" in output
        assert "_No affected components identified._" in output


class TestJsonExporter:
    """Tests for the JSON exporter."""

    def test_export_valid_json(self, sample_analysis_result):
        """Export should produce valid JSON."""
        exporter = JsonExporter()
        output = exporter.export(sample_analysis_result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_export_roundtrip(self, sample_analysis_result):
        """JSON output should roundtrip back to a FailureAnalysisResult."""
        exporter = JsonExporter()
        output = exporter.export(sample_analysis_result)
        parsed = json.loads(output)
        restored = FailureAnalysisResult.model_validate(parsed)
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
        assert isinstance(exporter, MarkdownExporter)

    def test_get_json_exporter(self):
        """Should return a JsonExporter for 'json'."""
        exporter = get_exporter("json")
        assert isinstance(exporter, JsonExporter)

    def test_case_insensitive(self):
        """Format name should be case-insensitive."""
        exporter = get_exporter("MARKDOWN")
        assert isinstance(exporter, MarkdownExporter)

    def test_unsupported_format_raises(self):
        """Unsupported format should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            get_exporter("pdf")
