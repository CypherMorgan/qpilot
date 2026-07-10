"""Tests for the Failure Analysis service layer.

Uses mocked AI provider and prompt manager to verify service
orchestration without real API calls or database.
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.exceptions import (
    InvalidResponseError,
    NotFoundError,
    ProviderUnavailableError,
)
from app.modules.failure_analysis.models import (
    AnalysisRequest,
    InputSourceType,
)
from app.modules.failure_analysis.service import FailureAnalysisService


class TestAnalyze:
    """Tests for FailureAnalysisService.analyze()."""

    async def test_analyze_success(self, mock_provider, mock_registry, mock_prompt_manager):
        """Happy path: valid input returns a complete AnalysisResponse."""
        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )

        # We need to mock the repository's create to return a session-like object
        fake_session = AsyncMock()
        fake_session.id = UUID("00000000-0000-0000-0000-000000000001")
        service._repository.create = AsyncMock(return_value=fake_session)
        service._repository.update = AsyncMock(return_value=fake_session)

        request = AnalysisRequest(
            content="AssertionError: expected 200, got 500",
            source_type=InputSourceType.PLAIN_TEXT,
        )

        response = await service.analyze(request)

        assert response.session_id == fake_session.id
        assert response.status == "completed"
        assert response.result is not None
        assert response.provider == "mock"
        assert response.total_tokens > 0
        assert response.latency_ms > 0

    async def test_analyze_marks_session_failed_on_error(self, mock_prompt_manager, mock_registry):
        """When the provider throws, the session should be marked as FAILED."""
        # Create a provider that raises an error
        failing_provider = AsyncMock()
        failing_provider.name = "mock"

        async def failing_generate(request):
            raise ProviderUnavailableError("Provider is down")

        failing_provider.generate = failing_generate
        mock_registry.register("failing", failing_provider)

        fake_session = AsyncMock()
        fake_session.id = UUID("00000000-0000-0000-0000-000000000002")
        fake_repo = AsyncMock()
        fake_repo.create = AsyncMock(return_value=fake_session)
        fake_repo.update = AsyncMock(return_value=fake_session)

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="failing",
        )
        service._repository = fake_repo

        request = AnalysisRequest(content="Test input.")

        with pytest.raises(ProviderUnavailableError):
            await service.analyze(request)

        # Verify update was called with FAILED status
        update_call = fake_repo.update.call_args
        assert update_call is not None
        assert update_call[0][0] == fake_session.id
        assert update_call[0][1]["status"].value == "failed"

    async def test_analyze_invalid_response(self, mock_prompt_manager, mock_registry):
        """When the provider returns unparseable content, raise InvalidResponseError."""
        invalid_provider = AsyncMock()
        invalid_provider.name = "mock"

        async def invalid_generate(request):
            from app.ai.models import AIResponse, ProviderMetadata, TokenUsage
            return AIResponse(
                content="This is not JSON",
                parsed=None,
                usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                provider=ProviderMetadata(provider_name="mock", model="mock", latency_ms=5),
            )

        invalid_provider.generate = invalid_generate
        mock_registry.register("invalid", invalid_provider)

        fake_session = AsyncMock()
        fake_session.id = UUID("00000000-0000-0000-0000-000000000003")
        fake_repo = AsyncMock()
        fake_repo.create = AsyncMock(return_value=fake_session)
        fake_repo.update = AsyncMock(return_value=fake_session)

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="invalid",
        )
        service._repository = fake_repo

        request = AnalysisRequest(content="Test input.")

        with pytest.raises(InvalidResponseError):
            await service.analyze(request)

    async def test_analyze_with_missing_provider(self, mock_prompt_manager):
        """When the provider is not registered, raise ProviderUnavailableError."""
        from app.ai.registry import ProviderRegistry

        empty_registry = ProviderRegistry()

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=empty_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="nonexistent",
        )

        request = AnalysisRequest(content="Test input.")

        with pytest.raises(ProviderUnavailableError, match="Unknown provider"):
            await service.analyze(request)


class TestGetSession:
    """Tests for FailureAnalysisService.get_session()."""

    async def test_get_existing_session(self, mock_provider, mock_registry, mock_prompt_manager):
        """Getting an existing session with output_data should return the analysis."""
        session_id = UUID("00000000-0000-0000-0000-000000000010")

        from app.domain.models import AnalysisStatus, AnalysisType
        from app.infrastructure.models.analysis_session import AnalysisSession

        fake_session = AnalysisSession(
            id=session_id,
            title="Test Session",
            analysis_type=AnalysisType.FAILURE_ANALYSIS,
            status=AnalysisStatus.COMPLETED,
            output_data={
                "input_summary": "Test summary.",
                "summary": "A test summary.",
                "root_causes": [],
                "suggested_fixes": [],
                "affected_components": [],
                "test_failures": [],
                "environment_details": [],
                "recommendations": [],
                "related_tests": [],
            },
            provider_used="mock",
            model_used="mock-model",
            total_tokens=150,
            latency_ms=42,
        )

        fake_repo = AsyncMock()
        fake_repo.get_with_output = AsyncMock(return_value=fake_session)

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )

        service._repository = fake_repo

        response = await service.get_session(session_id)

        assert response.session_id == session_id
        assert response.status == "completed"
        assert response.provider == "mock"
        assert response.result.input_summary == "Test summary."

    async def test_get_missing_session(self, mock_provider, mock_registry, mock_prompt_manager):
        """Getting a non-existent session should raise NotFoundError."""
        fake_repo = AsyncMock()
        fake_repo.get_with_output = AsyncMock(return_value=None)

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )
        service._repository = fake_repo

        session_id = UUID("00000000-0000-0000-0000-000000000099")

        with pytest.raises(NotFoundError, match="Analysis session not found"):
            await service.get_session(session_id)

    async def test_get_session_no_output(self, mock_provider, mock_registry, mock_prompt_manager):
        """A session without output_data should raise NotFoundError."""
        from app.domain.models import AnalysisStatus, AnalysisType
        from app.infrastructure.models.analysis_session import AnalysisSession

        session_id = UUID("00000000-0000-0000-0000-000000000020")
        fake_session = AnalysisSession(
            id=session_id,
            title="Pending",
            analysis_type=AnalysisType.FAILURE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            output_data=None,
        )

        fake_repo = AsyncMock()
        fake_repo.get_with_output = AsyncMock(return_value=fake_session)

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )
        service._repository = fake_repo

        with pytest.raises(NotFoundError, match="has no output data"):
            await service.get_session(session_id)


class TestListSessions:
    """Tests for FailureAnalysisService.list_sessions()."""

    async def test_list_empty(self, mock_provider, mock_registry, mock_prompt_manager):
        """Listing when there are no sessions should return empty list."""
        fake_repo = AsyncMock()
        fake_repo.list_sessions = AsyncMock(return_value=([], 0))

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )
        service._repository = fake_repo

        items, total = await service.list_sessions()
        assert items == []
        assert total == 0

    async def test_list_with_items(self, mock_provider, mock_registry, mock_prompt_manager, sample_analysis_result):
        """Listing should return session items."""
        from datetime import datetime

        from app.modules.failure_analysis.models import AnalysisSessionListItem

        fake_items = [
            AnalysisSessionListItem(
                session_id=UUID("00000000-0000-0000-0000-000000000030"),
                title="Test Session",
                status="completed",
                created_at=datetime(2026, 7, 1),
                updated_at=datetime(2026, 7, 1),
                input_summary="Test summary.",
            ),
        ]

        fake_repo = AsyncMock()
        fake_repo.list_sessions = AsyncMock(return_value=(fake_items, 1))

        service = FailureAnalysisService(
            db_session=AsyncMock(),
            provider_registry=mock_registry,
            prompt_manager=mock_prompt_manager,
            active_provider="mock",
        )
        service._repository = fake_repo

        items, total = await service.list_sessions()
        assert len(items) == 1
        assert total == 1
        assert items[0].title == "Test Session"
