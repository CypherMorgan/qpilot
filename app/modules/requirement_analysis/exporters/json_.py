"""JSON exporter for Requirement Analysis results.

Produces a pretty-printed JSON string of the analysis result.
"""

from __future__ import annotations

import json

from app.modules.requirement_analysis.exporters.base import AnalysisExporter
from app.modules.requirement_analysis.models import RequirementAnalysisResult


class JsonExporter(AnalysisExporter):
    """Exports analysis results as pretty-printed JSON."""

    def export(self, result: RequirementAnalysisResult) -> str:
        """Convert the analysis result to formatted JSON."""
        return json.dumps(
            result.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
