"""Markdown exporter for Failure Analysis results.

Produces a well-structured Markdown document suitable for sharing
in documentation, PRs, or issue trackers.
"""

from __future__ import annotations

from app.modules.failure_analysis.exporters.base import FailureExporter
from app.modules.failure_analysis.models import (
    AffectedComponent,
    FailureAnalysisResult,
    RootCause,
    SuggestedFix,
    TestFailure,
)


class MarkdownExporter(FailureExporter):
    """Exports analysis results as a formatted Markdown document."""

    def export(self, result: FailureAnalysisResult) -> str:
        """Convert the analysis result to Markdown."""
        lines: list[str] = []

        lines.append("# Automation Failure Analysis Report")
        lines.append("")
        lines.append(f"**Input summary:** {result.input_summary}")
        lines.append(f"**Analysis timestamp:** {result.analysis_timestamp.isoformat()}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(result.summary)
        lines.append("")

        lines.extend(self._export_root_causes(result.root_causes))
        lines.extend(self._export_suggested_fixes(result.suggested_fixes))
        lines.extend(self._export_affected_components(result.affected_components))
        lines.extend(self._export_test_failures(result.test_failures))
        lines.extend(self._export_environment_details(result.environment_details))
        lines.extend(self._export_recommendations(result.recommendations))
        lines.extend(self._export_related_tests(result.related_tests))

        return "\n".join(lines)

    # ── Section builders ────────────────────────────────────────

    def _export_root_causes(self, causes: list[RootCause]) -> list[str]:
        lines = ["## Root Causes", ""]
        for rc in causes:
            lines.append(f"### {rc.id}: {rc.title}")
            lines.append("")
            lines.append(f"{rc.description}")
            lines.append("")
            lines.append(f"  - **Category:** `{rc.category}`")
            lines.append(f"  - **Severity:** `{rc.severity}`")
            if rc.failing_file:
                lines.append(f"  - **Failing file:** `{rc.failing_file}`")
                if rc.failing_line:
                    lines.append(f"  - **Line:** {rc.failing_line}")
            if rc.error_message:
                lines.append("")
                lines.append("**Error message:**")
                lines.append(f"```\n{rc.error_message}\n```")
            if rc.stack_trace:
                lines.append("")
                lines.append("**Stack trace:**")
                for frame in rc.stack_trace:
                    location = f"{frame.file}:{frame.line}"
                    if frame.function:
                        location += f" in {frame.function}"
                    lines.append(f"  - `{location}`")
                    if frame.code:
                        lines.append(f"    `{frame.code}`")
            lines.append("")
        if not causes:
            lines.append("_No root causes identified._")
            lines.append("")
        return lines

    def _export_suggested_fixes(self, fixes: list[SuggestedFix]) -> list[str]:
        lines = ["## Suggested Fixes", ""]
        for fix in fixes:
            lines.append(f"### {fix.id}: {fix.description}")
            lines.append("")
            lines.append(f"  - **Root cause:** {fix.root_cause_id}")
            lines.append(f"  - **Priority:** `{fix.priority}`")
            lines.append(f"  - **Effort:** {fix.effort_estimate}")
            if fix.related_files:
                lines.append("  - **Files to modify:**")
                for f in fix.related_files:
                    lines.append(f"    - `{f}`")
            if fix.code_example:
                lines.append("")
                lines.append("**Code fix:**")
                lines.append(f"```\n{fix.code_example}\n```")
            lines.append("")
        if not fixes:
            lines.append("_No suggested fixes identified._")
            lines.append("")
        return lines

    def _export_affected_components(self, components: list[AffectedComponent]) -> list[str]:
        lines = ["## Affected Components", ""]
        lines.append("| ID | Component | Impact | Related Root Causes |")
        lines.append("|----|-----------|--------|---------------------|")
        for cmp in components:
            related = ", ".join(cmp.related_root_causes) if cmp.related_root_causes else "-"
            lines.append(f"| {cmp.id} | {cmp.name} | {cmp.impact} | {related} |")
        lines.append("")
        if not components:
            lines.append("_No affected components identified._")
            lines.append("")
        return lines

    def _export_test_failures(self, failures: list[TestFailure]) -> list[str]:
        lines = ["## Test Failures", ""]
        for tf in failures:
            lines.append(f"### {tf.id}: {tf.test_name}")
            lines.append("")
            if tf.test_file:
                lines.append(f"  - **File:** `{tf.test_file}`")
            if tf.duration_seconds is not None:
                lines.append(f"  - **Duration:** {tf.duration_seconds}s")
            if tf.retry_count > 0:
                lines.append(f"  - **Retries:** {tf.retry_count}")
            if tf.error_message:
                lines.append("")
                lines.append("**Error:**")
                lines.append(f"```\n{tf.error_message}\n```")
            lines.append("")
        if not failures:
            lines.append("_No individual test failures listed._")
            lines.append("")
        return lines

    def _export_environment_details(self, details: list[str]) -> list[str]:
        lines = ["## Environment Details", ""]
        for i, d in enumerate(details, 1):
            lines.append(f"{i}. {d}")
        lines.append("")
        if not details:
            lines.append("_No environment details recorded._")
            lines.append("")
        return lines

    def _export_recommendations(self, recommendations: list[str]) -> list[str]:
        lines = ["## Recommendations", ""]
        for i, r in enumerate(recommendations, 1):
            lines.append(f"{i}. {r}")
        lines.append("")
        if not recommendations:
            lines.append("_No recommendations provided._")
            lines.append("")
        return lines

    def _export_related_tests(self, tests: list[str]) -> list[str]:
        lines = ["## Related Tests", ""]
        for i, t in enumerate(tests, 1):
            lines.append(f"{i}. {t}")
        lines.append("")
        if not tests:
            lines.append("_No related tests identified._")
            lines.append("")
        return lines
