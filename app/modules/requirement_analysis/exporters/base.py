"""Abstract base class for requirement analysis exporters.

Every exporter implements the ``export()`` method that converts a
``RequirementAnalysisResult`` into a string (Markdown, JSON, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.requirement_analysis.models import RequirementAnalysisResult


class AnalysisExporter(ABC):
    """Abstract base for all export formats."""

    @abstractmethod
    def export(self, result: RequirementAnalysisResult) -> str:
        """Convert the analysis result to the target format.

        Args:
            result: The structured analysis result to export.

        Returns:
            The analysis as a formatted string.
        """
