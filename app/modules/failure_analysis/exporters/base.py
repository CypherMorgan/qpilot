"""Abstract base class for failure analysis exporters.

Every exporter implements the ``export()`` method that converts a
``FailureAnalysisResult`` into a string (Markdown, JSON, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.failure_analysis.models import FailureAnalysisResult


class FailureExporter(ABC):
    """Abstract base for all export formats."""

    @abstractmethod
    def export(self, result: FailureAnalysisResult) -> str:
        """Convert the analysis result to the target format.

        Args:
            result: The structured analysis result to export.

        Returns:
            The analysis as a formatted string.
        """
