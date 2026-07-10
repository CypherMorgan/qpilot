"""Automation Failure Analysis Module.

Provides AI-powered analysis of CI/CD test failures, error traces,
and test run logs, producing structured output with root cause
analysis, suggested fixes, and affected component identification.

Public API:
    - ``FailureAnalysisResult`` — the complete structured output
    - ``AnalysisRequest`` — input schema for the analysis endpoint
    - ``router`` — FastAPI router with analysis endpoints
    - ``FailureAnalysisService`` — business logic orchestrator
"""

from app.modules.failure_analysis.models import (
    AnalysisRequest,
    FailureAnalysisResult,
)
from app.modules.failure_analysis.router import router
from app.modules.failure_analysis.service import FailureAnalysisService

__all__ = [
    "AnalysisRequest",
    "FailureAnalysisResult",
    "FailureAnalysisService",
    "router",
]
