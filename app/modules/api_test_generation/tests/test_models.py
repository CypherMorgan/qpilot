"""Tests for API Test Generation Pydantic models."""

from __future__ import annotations

from datetime import UTC

import pytest
from pydantic import ValidationError

from app.modules.api_test_generation.models import (
    EndpointGenInfo,
    GeneratedFile,
    OpenApiGenerateRequest,
    OpenApiGenerateResponse,
    OpenApiSessionListItem,
)


class TestOpenApiGenerateRequest:
    """Tests for the input request model."""

    def test_valid_minimal(self):
        """A request with just spec content should be valid."""
        request = OpenApiGenerateRequest(spec="openapi: 3.1.0")
        assert request.spec == "openapi: 3.1.0"
        assert request.spec_format == "yaml"
        assert request.title is None
        assert request.paths is None
        assert request.context is None

    def test_valid_full(self):
        """A request with all fields should be valid."""
        request = OpenApiGenerateRequest(
            spec='{"openapi": "3.1.0"}',
            spec_format="json",
            title="My API Tests",
            paths=["/pets", "/users"],
            context="Async stack",
        )
        assert request.spec_format == "json"
        assert request.title == "My API Tests"
        assert request.paths == ["/pets", "/users"]
        assert request.context == "Async stack"

    def test_empty_spec_rejected(self):
        """An empty spec string should be rejected."""
        with pytest.raises(ValidationError):
            OpenApiGenerateRequest(spec="")

    def test_spec_too_long_rejected(self):
        """A spec exceeding 500,000 characters should be rejected."""
        with pytest.raises(ValidationError):
            OpenApiGenerateRequest(spec="x" * 500_001)

    def test_invalid_spec_format_rejected(self):
        """An invalid spec_format value should be rejected."""
        with pytest.raises(ValidationError):
            OpenApiGenerateRequest(spec="openapi: 3.1.0", spec_format="toml")

    def test_title_max_length(self):
        """Title exceeding 255 chars should be rejected."""
        with pytest.raises(ValidationError):
            OpenApiGenerateRequest(spec="openapi: 3.1.0", title="x" * 256)

    def test_context_max_length(self):
        """Context exceeding 10,000 chars should be rejected."""
        with pytest.raises(ValidationError):
            OpenApiGenerateRequest(spec="openapi: 3.1.0", context="x" * 10_001)

    def test_paths_empty_list_allowed(self):
        """An empty paths list should be allowed (means all endpoints)."""
        request = OpenApiGenerateRequest(spec="openapi: 3.1.0", paths=[])
        assert request.paths == []


class TestGeneratedFile:
    """Tests for the generated file metadata model."""

    def test_minimal(self):
        """A file with just filename should be valid."""
        f = GeneratedFile(filename="test_pets.py", path="generated-tests/test_pets.py")
        assert f.size == 0
        assert f.content == ""

    def test_full(self):
        """A file with all fields should be valid."""
        f = GeneratedFile(
            filename="test_pets.py",
            path="generated-tests/test_pets.py",
            size=1024,
            content="print('hello')",
        )
        assert f.size == 1024
        assert f.content == "print('hello')"


class TestEndpointGenInfo:
    """Tests for per-endpoint generation info."""

    def test_minimal(self):
        """An endpoint info with just path and method should be valid."""
        info = EndpointGenInfo(path="/pets", method="get")
        assert info.tests_generated == 0

    def test_full(self):
        """An endpoint info with all fields should be valid."""
        info = EndpointGenInfo(path="/pets/{id}", method="get", tests_generated=5)
        assert info.tests_generated == 5


class TestOpenApiGenerateResponse:
    """Tests for the generation response model."""

    def test_minimal(self):
        """A response with just required fields should be valid."""
        from uuid import uuid4
        response = OpenApiGenerateResponse(
            session_id=uuid4(),
            status="completed",
        )
        assert response.spec_title == ""
        assert response.spec_version == ""
        assert response.endpoint_count == 0
        assert response.files == []
        assert response.endpoints == []
        assert response.download_url == ""

    def test_serialization_roundtrip(self):
        """Response should survive model_dump and model_validate roundtrip."""
        from uuid import uuid4

        response = OpenApiGenerateResponse(
            session_id=uuid4(),
            status="completed",
            spec_title="Pet Store",
            spec_version="1.0.0",
            endpoint_count=6,
            files=[
                GeneratedFile(filename="test_pets.py", path="generated-tests/test_pets.py", size=100),
                GeneratedFile(filename="conftest.py", path="generated-tests/conftest.py", size=200),
            ],
            endpoints=[
                EndpointGenInfo(path="/pets", method="get", tests_generated=4),
            ],
            download_url="/api/v1/openapi/sessions/abc/download",
            provider="openrouter",
            model="gpt-4o-mini",
            total_tokens=800,
            latency_ms=1500,
        )
        data = response.model_dump(mode="json")
        restored = OpenApiGenerateResponse.model_validate(data)
        assert restored.session_id == response.session_id
        assert restored.spec_title == "Pet Store"
        assert len(restored.files) == 2
        assert restored.endpoint_count == 6


class TestOpenApiSessionListItem:
    """Tests for the session list item model."""

    def test_minimal(self):
        """A session list item with just required fields should be valid."""
        from datetime import datetime
        from uuid import uuid4

        now = datetime.now(UTC)
        item = OpenApiSessionListItem(
            session_id=uuid4(),
            status="completed",
            created_at=now,
            updated_at=now,
        )
        assert item.title is None
        assert item.spec_title is None
        assert item.endpoint_count == 0
        assert item.file_count == 0
