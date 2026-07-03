"""Markdown exporter for Requirement Analysis results.

Produces a well-structured Markdown document suitable for sharing
in documentation, PRs, or issue trackers.
"""

from __future__ import annotations

from typing import Any

from app.modules.requirement_analysis.exporters.base import AnalysisExporter
from app.modules.requirement_analysis.models import (
    AutomationCandidate,
    BoundaryTestCase,
    EdgeCase,
    FunctionalTestCase,
    MissingRequirement,
    NegativeTestCase,
    PriorityAssessment,
    RequirementAnalysisResult,
    Risk,
)


class MarkdownExporter(AnalysisExporter):
    """Exports analysis results as a formatted Markdown document."""

    def export(self, result: RequirementAnalysisResult) -> str:
        """Convert the analysis result to Markdown."""
        lines: list[str] = []

        lines.append("# Requirement Analysis Report")
        lines.append("")
        lines.append(f"**Input summary:** {result.input_summary}")
        lines.append(f"**Analysis timestamp:** {result.analysis_timestamp.isoformat()}")
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.extend(self._export_functional_tests(result.functional_tests))
        lines.extend(self._export_negative_tests(result.negative_tests))
        lines.extend(self._export_boundary_tests(result.boundary_tests))
        lines.extend(self._export_edge_cases(result.edge_cases))
        lines.extend(self._export_assumptions(result.assumptions))
        lines.extend(self._export_risks(result.risks))
        lines.extend(self._export_missing_requirements(result.missing_requirements))
        lines.extend(self._export_suggested_questions(result.suggested_questions))
        lines.extend(self._export_automation_candidates(result.automation_candidates))
        lines.extend(self._export_priority_assessment(result.priority_assessment))

        return "\n".join(lines)

    # ── Section builders ────────────────────────────────────────

    def _export_functional_tests(self, tests: list[FunctionalTestCase]) -> list[str]:
        lines = ["## Functional Test Cases", ""]
        for tc in tests:
            lines.extend(self._render_test_case(tc))
        if not tests:
            lines.append("_No functional test cases identified._")
            lines.append("")
        return lines

    def _export_negative_tests(self, tests: list[NegativeTestCase]) -> list[str]:
        lines = ["## Negative Test Cases", ""]
        for tc in tests:
            lines.extend(self._render_test_case(tc))
        if not tests:
            lines.append("_No negative test cases identified._")
            lines.append("")
        return lines

    def _export_boundary_tests(self, tests: list[BoundaryTestCase]) -> list[str]:
        lines = ["## Boundary Tests", ""]
        for tc in tests:
            lines.extend(self._render_test_case(tc))
            if tc.boundary_value:
                lines.append(f"  - **Boundary value:** `{tc.boundary_value}`")
            lines.append("")
        if not tests:
            lines.append("_No boundary tests identified._")
            lines.append("")
        return lines

    def _export_edge_cases(self, cases: list[EdgeCase]) -> list[str]:
        lines = ["## Edge Cases", ""]
        for ec in cases:
            lines.append(f"### {ec.id}: {ec.title}")
            lines.append("")
            lines.append(f"{ec.description}")
            lines.append("")
            lines.append(f"  - **Impact:** {ec.impact}")
            if ec.recommendation:
                lines.append(f"  - **Recommendation:** {ec.recommendation}")
            lines.append("")
        if not cases:
            lines.append("_No edge cases identified._")
            lines.append("")
        return lines

    def _export_assumptions(self, assumptions: list[str]) -> list[str]:
        lines = ["## Assumptions", ""]
        for i, a in enumerate(assumptions, 1):
            lines.append(f"{i}. {a}")
        lines.append("")
        if not assumptions:
            lines.append("_No assumptions recorded._")
            lines.append("")
        return lines

    def _export_risks(self, risks: list[Risk]) -> list[str]:
        lines = ["## Risks", ""]
        for r in risks:
            lines.append(f"### {r.id}: {r.description}")
            lines.append("")
            lines.append(f"  - **Severity:** `{r.severity}`")
            lines.append(f"  - **Likelihood:** {r.likelihood}")
            if r.mitigation:
                lines.append(f"  - **Mitigation:** {r.mitigation}")
            lines.append("")
        if not risks:
            lines.append("_No risks identified._")
            lines.append("")
        return lines

    def _export_missing_requirements(self, reqs: list[MissingRequirement]) -> list[str]:
        lines = ["## Missing Requirements", ""]
        for mr in reqs:
            lines.append(f"### {mr.id}: {mr.topic}")
            lines.append("")
            lines.append(f"{mr.description}")
            lines.append("")
            lines.append(f"  - **Importance:** `{mr.importance}`")
            lines.append("")
        if not reqs:
            lines.append("_No missing requirements detected._")
            lines.append("")
        return lines

    def _export_suggested_questions(self, questions: list[str]) -> list[str]:
        lines = ["## Suggested Questions", ""]
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")
        if not questions:
            lines.append("_No suggested questions._")
            lines.append("")
        return lines

    def _export_automation_candidates(self, candidates: list[AutomationCandidate]) -> list[str]:
        lines = ["## Automation Candidates", ""]
        lines.append("| ID | Test Case | Feasibility | Effort | Value |")
        lines.append("|----|-----------|-------------|--------|-------|")
        for ac in candidates:
            lines.append(
                f"| {ac.id} | {ac.test_case_id} | {ac.feasibility} | "
                f"{ac.effort_estimate} | {ac.value_reason} |"
            )
        lines.append("")
        if not candidates:
            lines.append("_No automation candidates identified._")
            lines.append("")
        return lines

    def _export_priority_assessment(self, pa: PriorityAssessment) -> list[str]:
        lines = ["## Priority Assessment", ""]
        lines.append(f"**Overall priority:** `{pa.overall_priority}`")
        lines.append("")
        lines.append("### Critical Path Items")
        for item in pa.critical_path_items:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("### Quick Wins")
        for item in pa.quick_wins:
            lines.append(f"- {item}")
        lines.append("")
        lines.append(f"**Reasoning:** {pa.reasoning}")
        lines.append("")
        return lines

    # ── Helpers ─────────────────────────────────────────────────

    def _render_test_case(self, tc: Any) -> list[str]:
        """Render a generic test case (functional, negative, or boundary)."""
        lines = [
            f"### {tc.id}: {tc.title}",
            "",
            f"{tc.description}",
            "",
            "**Preconditions:**",
        ]
        if tc.preconditions:
            for p in tc.preconditions:
                lines.append(f"- {p}")
        else:
            lines.append("_None_")

        lines.append("")
        lines.append("**Steps:**")
        for i, step in enumerate(tc.steps, 1):
            lines.append(f"{i}. {step}")

        lines.append("")
        lines.append(f"**Expected result:** {tc.expected_result}")
        lines.append("")
        lines.append(f"**Priority:** `{tc.priority}`")
        if tc.tags:
            lines.append(f"**Tags:** `{', '.join(tc.tags)}`")
        lines.append("")
        return lines
