"""Tests for the API Test Generation service."""

from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AnalysisStatus, AnalysisType
from app.exceptions import (
    AnalysisError,
    NotFoundError,
    ProviderUnavailableError,
)
from app.infrastructure.models.analysis_session import AnalysisSession
from app.modules.api_test_generation.models import (
    OpenApiGenerateRequest,
    OpenApiGenerateResponse,
    OpenApiSessionListItem,
)
from app.modules.api_test_generation.service import (
    ApiTestGenerationService,
)


class TestApiTestGenerationService:
    """Tests for the API test generation service."""

    @pytest.fixture
    def db_session(self):
        """Create a mock async DB session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, db_session, mock_registry, mock_prompt_manager):
        """Create a service with a mock registry and mock prompt manager."""
        registry = mock_registry()
        svc = ApiTestGenerationService(
            db_session=db_session,
            provider_registry=registry,
            prompt_manager=mock_prompt_manager,
            active_provider="test-provider",
        )
        # Replace the real repository with a mock for test assertions
        svc._repository = AsyncMock()
        svc._repository.create.return_value = AnalysisSession(
            id=uuid4(),
            title="Test",
            analysis_type=AnalysisType.API_TEST_GENERATION,
            status=AnalysisStatus.PROCESSING,
            input_content="spec",
            input_source_type="openapi_yaml",
        )
        svc._repository.update.return_value = AnalysisSession(
            id=uuid4(),
            title="Test",
            analysis_type=AnalysisType.API_TEST_GENERATION,
            status=AnalysisStatus.COMPLETED,
            output_data={"spec_title": "Pet Store API", "spec_version": "1.0.0"},
            provider_used="test-provider",
            model_used="test-model",
            total_tokens=800,
            latency_ms=500,
        )
        return svc

    @pytest.fixture
    def analyze_request(self, petstore_yaml):
        """Create a standard analyze request."""
        return OpenApiGenerateRequest(
            spec=petstore_yaml,
            spec_format="yaml",
            title="Pet Store Tests",
        )

    async def test_analyze_success(self, service, analyze_request):
        """A successful analysis should return a valid response with files."""
        result = await service.analyze(analyze_request)

        assert isinstance(result, OpenApiGenerateResponse)
        assert result.status == "completed"
        assert result.spec_title == "Pet Store API"
        assert result.spec_version == "1.0.0"
        assert result.endpoint_count == 6
        assert len(result.files) > 0
        assert result.provider == "test-provider"

        # Should have conftest.py and README.md plus test files
        filenames = [f.filename for f in result.files]
        assert "conftest.py" in filenames
        assert "README.md" in filenames

    async def test_analyze_persists_session(self, service, analyze_request):
        """The session should be persisted with correct status."""
        result = await service.analyze(analyze_request)

        # If analysis succeeds, status must be "completed"
        assert result.status == "completed"
        assert result.provider == "test-provider"
        assert result.total_tokens > 0

    async def test_analyze_with_path_filter(self, service, petstore_yaml):
        """Filtering by specific paths should only include those endpoints."""
        request = OpenApiGenerateRequest(
            spec=petstore_yaml,
            spec_format="yaml",
            paths=["/pets", "/pets/{petId}"],
        )
        result = await service.analyze(request)

        assert result.endpoint_count == 4  # GET, POST /pets + GET, DELETE /pets/{petId}

    async def test_analyze_with_empty_paths(self, service, petstore_yaml):
        """Empty paths filter (list) should mean no filter -- all endpoints returned."""
        request = OpenApiGenerateRequest(
            spec=petstore_yaml,
            spec_format="yaml",
            paths=[],
        )

        # Empty list means no filter -- all endpoints are included
        result = await service.analyze(request)
        assert result.endpoint_count == 6  # All petstore endpoints

    async def test_analyze_with_nonexistent_path_filter(self, service, petstore_yaml):
        """Filter with paths that don't exist should raise error."""
        request = OpenApiGenerateRequest(
            spec=petstore_yaml,
            spec_format="yaml",
            paths=["/nonexistent"],
        )

        with pytest.raises(AnalysisError, match="No endpoints found"):
            await service.analyze(request)

    async def test_analyze_marks_session_failed_on_error(
        self, service, analyze_request
    ):
        """When analysis fails, the session should be marked as FAILED."""
        # Make provider unavailable
        service._provider_registry.get.side_effect = ProviderUnavailableError(
            "Provider not available"
        )

        with pytest.raises(ProviderUnavailableError):
            await service.analyze(analyze_request)

        # The error path should call update at least once (to mark session as failed)
        assert service._repository.update.called

    async def test_analyze_missing_provider(self, service, analyze_request):
        """An unregistered provider should raise ProviderUnavailableError."""
        service._active_provider = "nonexistent"
        service._provider_registry.get.side_effect = ProviderUnavailableError(
            "Provider 'nonexistent' not registered"
        )

        with pytest.raises(ProviderUnavailableError):
            await service.analyze(analyze_request)

    async def test_analyze_invalid_spec(self, service):
        """An invalid spec should raise AnalysisError."""
        request = OpenApiGenerateRequest(
            spec="invalid: yaml: content: [",
            spec_format="yaml",
        )

        with pytest.raises(AnalysisError):
            await service.analyze(request)

    async def test_get_session_found(self, service):
        """Getting an existing session should return the result."""
        # Setup mock repository to return a session
        session_id = uuid4()
        service._repository.get_with_output = AsyncMock(
            return_value=AnalysisSession(
                id=session_id,
                title="Test",
                analysis_type=AnalysisType.API_TEST_GENERATION,
                status=AnalysisStatus.COMPLETED,
                output_data={
                    "spec_title": "Pet Store API",
                    "spec_version": "1.0.0",
                    "endpoint_count": 6,
                    "files": [],
                    "endpoints": [],
                    "zip_content": "base64encoded",
                },
                provider_used="test-provider",
                model_used="test-model",
                total_tokens=800,
                latency_ms=500,
            )
        )

        result = await service.get_session(session_id)
        assert isinstance(result, OpenApiGenerateResponse)
        assert result.spec_title == "Pet Store API"

    async def test_get_session_not_found(self, service):
        """Getting a nonexistent session should raise NotFoundError."""
        service._repository.get_with_output = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError, match="not found"):
            await service.get_session(uuid4())

    async def test_get_session_no_output(self, service):
        """Getting a session without output data should raise NotFoundError."""
        session_id = uuid4()
        service._repository.get_with_output = AsyncMock(
            return_value=AnalysisSession(
                id=session_id,
                title="Test",
                analysis_type=AnalysisType.API_TEST_GENERATION,
                status=AnalysisStatus.FAILED,
                output_data=None,
            )
        )

        with pytest.raises(NotFoundError, match="no output data"):
            await service.get_session(session_id)

    async def test_list_sessions_empty(self, service):
        """Listing sessions when none exist should return empty list."""
        service._repository.list_sessions = AsyncMock(return_value=([], 0))

        items, total = await service.list_sessions()
        assert items == []
        assert total == 0

    async def test_list_sessions_with_items(self, service):
        """Listing sessions with items should return them."""
        from datetime import datetime
        now = datetime.now(UTC)
        service._repository.list_sessions = AsyncMock(
            return_value=(
                [
                    OpenApiSessionListItem(
                        session_id=uuid4(),
                        status="completed",
                        spec_title="Pet Store API",
                        endpoint_count=6,
                        created_at=now,
                        updated_at=now,
                    )
                ],
                1,
            )
        )

        items, total = await service.list_sessions()
        assert len(items) == 1
        assert total == 1
        assert items[0].spec_title == "Pet Store API"

    async def test_download_zip_found(self, service):
        """Downloading a ZIP for a valid session should return bytes."""
        session_id = uuid4()
        import base64
        zip_content = b"fake-zip-content"
        service._repository.get_with_output = AsyncMock(
            return_value=AnalysisSession(
                id=session_id,
                title="Test",
                analysis_type=AnalysisType.API_TEST_GENERATION,
                status=AnalysisStatus.COMPLETED,
                output_data={
                    "zip_content": base64.b64encode(zip_content).decode("ascii"),
                },
            )
        )

        result = await service.download_zip(session_id)
        assert result == zip_content

    async def test_download_zip_not_found(self, service):
        """Downloading a ZIP for a nonexistent session should return None."""
        service._repository.get_with_output = AsyncMock(return_value=None)

        result = await service.download_zip(uuid4())
        assert result is None

    async def test_analyze_conftest_included(self, service, analyze_request):
        """Generated output should include conftest.py with client fixture."""
        result = await service.analyze(analyze_request)

        conftest = next(
            (f for f in result.files if f.filename == "conftest.py"),
            None,
        )
        assert conftest is not None
        assert conftest.size > 0

    async def test_analyze_readme_included(self, service, analyze_request):
        """Generated output should include README.md."""
        result = await service.analyze(analyze_request)

        readme = next(
            (f for f in result.files if f.filename == "README.md"),
            None,
        )
        assert readme is not None
        assert readme.size > 0
