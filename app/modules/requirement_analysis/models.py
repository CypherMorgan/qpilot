"""Pydantic schemas for Requirement Analysis.

Every analysis produces a ``RequirementAnalysisResult`` with 10+
strongly typed sections.  These models are the contract between the
AI response parser, the service layer, and the export layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────

class PriorityLevel(str, Enum):
    """Priority level for test cases and assessments."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskSeverity(str, Enum):
    """Severity level for identified risks."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutomationFeasibility(str, Enum):
    """How feasible a test scenario is to automate."""

    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    NOT_FEASIBLE = "not_feasible"


class InputSourceType(str, Enum):
    """Supported input source types."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"


# ── Input schema ──────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """Input payload for the requirement analysis endpoint."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="The requirements text to analyze (plain text, Markdown, or acceptance criteria).",
    )
    source_type: InputSourceType = Field(
        default=InputSourceType.PLAIN_TEXT,
        description="The format of the input content.",
    )
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for the analysis session.",
    )
    context: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional additional context (e.g. tech stack, domain info).",
    )
    output_format: str = Field(
        default="json",
        description="Desired output format: 'json', 'markdown', or 'both'.",
    )


# ── Shared models ─────────────────────────────────────────────────

class TestCase(BaseModel):
    """Base model for a test case in any category."""

    id: str = Field(description="Unique identifier within the analysis (e.g. TC-FUNC-001).")
    title: str = Field(description="Short, descriptive title of the test scenario.")
    description: str = Field(description="Detailed explanation of what is being tested.")
    preconditions: list[str] = Field(
        default_factory=list,
        description="Conditions that must be true before the test can run.",
    )
    steps: list[str] = Field(
        min_length=1,
        description="Ordered list of steps to execute the test.",
    )
    expected_result: str = Field(description="What should happen when the test passes.")
    priority: PriorityLevel = Field(
        default=PriorityLevel.MEDIUM,
        description="Importance of this test scenario.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Categorization tags (e.g. ['login', 'security']).",
    )


class FunctionalTestCase(TestCase):
    """A test case describing expected functional behavior."""


class NegativeTestCase(TestCase):
    """A test case describing what should NOT happen (error handling, rejection)."""


class BoundaryTestCase(TestCase):
    """A test case focusing on edge values (min, max, just below, just above)."""

    boundary_value: str = Field(
        default="",
        description="The specific boundary value being tested (e.g. '255 characters').",
    )


class EdgeCase(BaseModel):
    """An edge case or unusual condition that should be considered."""

    id: str = Field(description="Unique identifier (e.g. EC-001).")
    title: str = Field(description="Short description of the edge case.")
    description: str = Field(description="Detailed explanation of the unusual condition.")
    impact: str = Field(
        default="",
        description="Potential impact if not handled.",
    )
    recommendation: str | None = Field(
        default=None,
        description="Suggested approach to handle this edge case.",
    )


class Risk(BaseModel):
    """A potential risk identified in the requirements."""

    id: str = Field(description="Unique identifier (e.g. RSK-001).")
    description: str = Field(description="What could go wrong.")
    severity: RiskSeverity = Field(description="How serious this risk is.")
    likelihood: str = Field(description="Probability estimate: 'high', 'medium', 'low'.")
    mitigation: str | None = Field(
        default=None,
        description="Suggested mitigation strategy.",
    )


class AutomationCandidate(BaseModel):
    """A test scenario that is a good candidate for automation."""

    id: str = Field(description="Unique identifier (e.g. AUTO-001).")
    test_case_id: str = Field(description="Reference to the original test case (e.g. TC-FUNC-001).")
    feasibility: AutomationFeasibility = Field(description="How feasible automation is.")
    effort_estimate: str = Field(description="Rough effort estimate (e.g. '2-4 hours').")
    value_reason: str = Field(description="Why this test should be automated.")


class PriorityAssessment(BaseModel):
    """Overall priority assessment of the requirements."""

    overall_priority: PriorityLevel = Field(
        description="Overall priority of the requirements."
    )
    critical_path_items: list[str] = Field(
        description="Test scenarios that must be validated before release.",
    )
    quick_wins: list[str] = Field(
        description="Low-effort, high-value test scenarios.",
    )
    reasoning: str = Field(
        description="Explanation of the priority assessment.",
    )


class MissingRequirement(BaseModel):
    """A requirement that appears to be missing from the input."""

    id: str = Field(description="Unique identifier (e.g. MR-001).")
    topic: str = Field(description="The area where something is missing.")
    description: str = Field(description="What is likely needed but not specified.")
    importance: PriorityLevel = Field(description="How important this missing piece is.")


# ── Root output model ─────────────────────────────────────────────

class RequirementAnalysisResult(BaseModel):
    """Complete structured output of a requirement analysis.

    This is the document produced by the AI and stored in
    ``AnalysisSession.output_data``.
    """

    # Metadata
    input_summary: str = Field(
        description="One-paragraph summary of what the input described."
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this analysis was generated.",
    )

    # Analysis sections
    functional_tests: list[FunctionalTestCase] = Field(
        description="Test cases describing expected functional behavior.",
    )
    negative_tests: list[NegativeTestCase] = Field(
        description="Test cases describing what should NOT happen.",
    )
    boundary_tests: list[BoundaryTestCase] = Field(
        description="Test cases focusing on boundary values.",
    )
    edge_cases: list[EdgeCase] = Field(
        description="Unusual conditions and edge cases.",
    )
    assumptions: list[str] = Field(
        description="Assumptions made during the analysis.",
    )
    risks: list[Risk] = Field(
        description="Potential risks identified in the requirements.",
    )
    missing_requirements: list[MissingRequirement] = Field(
        description="Requirements that appear to be missing or underspecified.",
    )
    suggested_questions: list[str] = Field(
        description="Questions to ask stakeholders to clarify ambiguities.",
    )
    automation_candidates: list[AutomationCandidate] = Field(
        description="Test scenarios recommended for automation.",
    )
    priority_assessment: PriorityAssessment = Field(
        description="Overall priority assessment of the requirements.",
    )


# ── API response schema ───────────────────────────────────────────

class AnalysisResponse(BaseModel):
    """API response after a successful requirement analysis."""

    session_id: UUID = Field(description="ID of the analysis session.")
    status: str = Field(description="Current status of the session.")
    result: RequirementAnalysisResult = Field(
        description="The complete analysis result."
    )
    provider: str | None = Field(default=None, description="AI provider used.")
    model: str | None = Field(default=None, description="AI model used.")
    total_tokens: int = Field(default=0, description="Total tokens consumed.")
    latency_ms: int = Field(default=0, description="AI call duration in milliseconds.")


class AnalysisSessionListItem(BaseModel):
    """Lightweight summary for listing past analysis sessions."""

    session_id: UUID
    title: str | None = None
    source_type: str | None = None
    status: str
    provider: str | None = None
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime
    input_summary: str | None = None
