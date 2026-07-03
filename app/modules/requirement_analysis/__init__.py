"""Requirement Analysis Module.

Provides AI-powered analysis of software requirements, producing
structured output with functional tests, negative tests, boundary
tests, edge cases, assumptions, risks, and more.

Public API:
    - ``RequirementAnalysisResult`` — the complete structured output
    - ``AnalysisRequest`` — input schema for the analysis endpoint
    - ``router`` — FastAPI router with analysis endpoints
    - ``RequirementAnalysisService`` — business logic orchestrator
"""

from app.modules.requirement_analysis.models import (
    AnalysisRequest,
    AutomationCandidate,
    BoundaryTestCase,
    EdgeCase,
    FunctionalTestCase,
    NegativeTestCase,
    PriorityAssessment,
    PriorityLevel,
    RequirementAnalysisResult,
    Risk,
    RiskSeverity,
)
from app.modules.requirement_analysis.router import router
from app.modules.requirement_analysis.service import RequirementAnalysisService

__all__ = [
    "AnalysisRequest",
    "AutomationCandidate",
    "BoundaryTestCase",
    "EdgeCase",
    "FunctionalTestCase",
    "NegativeTestCase",
    "PriorityAssessment",
    "PriorityLevel",
    "RequirementAnalysisResult",
    "RequirementAnalysisService",
    "Risk",
    "RiskSeverity",
    "router",
]
