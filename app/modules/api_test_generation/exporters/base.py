"""Abstract base class for test file exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TestExporter(ABC):
    """Abstract base for exporting generated test files.

    Implementations produce the final deliverable — a set of
    Python test files or an archive containing them.
    """

    @abstractmethod
    def generate_conftest(
        self,
        servers: list[str],
        security_schemes: dict[str, Any],
    ) -> str:
        """Generate the conftest.py content with shared fixtures.

        Args:
            servers: Base URLs for the API server.
            security_schemes: Security scheme definitions.

        Returns:
            Python source code for conftest.py.
        """
        ...

    @abstractmethod
    def generate_readme(
        self,
        spec_title: str,
        spec_version: str,
        servers: list[str],
        endpoint_count: int,
    ) -> str:
        """Generate a README with setup and usage instructions.

        Args:
            spec_title: The API title.
            spec_version: The API version.
            servers: Base URLs for the API server.
            endpoint_count: Number of endpoints covered.

        Returns:
            Markdown content for the README.
        """
        ...
