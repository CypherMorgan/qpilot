"""JSON exporter for Failure Analysis results.

Produces a pretty-printed JSON string of the analysis result.
"""

from __future__ import annotations

import json

from app.modules.failure_analysis.exporters.base import FailureExporter
from app.modules.failure_analysis.models import FailureAnalysisResult


class JsonExporter(FailureExporter):
    """Exports analysis results as pretty-printed JSON."""

    def export(self, result: FailureAnalysisResult) -> str:
        """Convert the analysis result to formatted JSON."""
        return json.dumps(
            result.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
