"""Generic repository tests.

Tests BaseRepository CRUD operations using AnalysisSession as the
concrete model.  All tests use an in-memory SQLite database via the
``db_manager`` and ``db_session`` fixtures from conftest.py.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AnalysisType
from app.infrastructure.models.analysis_session import AnalysisSession
from app.infrastructure.repository import BaseRepository


class SessionRepository(BaseRepository[AnalysisSession]):
    """Concrete repository for testing the generic BaseRepository."""

    model_class = AnalysisSession


# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
async def repo(db_session: AsyncSession) -> SessionRepository:
    """Return a repository backed by a test database session."""
    return SessionRepository(db_session)


@pytest.fixture
async def persisted_session(repo: SessionRepository) -> AnalysisSession:
    """Create and persist a sample AnalysisSession for tests that need data."""
    return await repo.create(
        AnalysisSession(
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            title="Test Session",
        )
    )


# ── Create ──────────────────────────────────────────────────────


class TestCreate:
    async def test_creates_and_assigns_id(self, repo: SessionRepository) -> None:
        """Create persists the model and assigns a UUID primary key."""
        entity = await repo.create(
            AnalysisSession(analysis_type=AnalysisType.REQUIREMENT_ANALYSIS)
        )
        assert entity.id is not None
        assert isinstance(entity.id, uuid.UUID)

    async def test_creates_with_title(
        self, repo: SessionRepository
    ) -> None:
        """Create preserves provided field values."""
        entity = await repo.create(
            AnalysisSession(
                analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
                title="My Analysis",
            )
        )
        assert entity.title == "My Analysis"

    async def test_creates_with_default_status(
        self, repo: SessionRepository
    ) -> None:
        """Create uses the model-level default for status."""
        entity = await repo.create(
            AnalysisSession(analysis_type=AnalysisType.API_TEST_GENERATION)
        )
        assert entity.status.value == "pending"


# ── Read ────────────────────────────────────────────────────────


class TestGet:
    async def test_get_existing(self, repo: SessionRepository,
                                persisted_session: AnalysisSession) -> None:
        """Get returns the entity for a valid UUID."""
        entity = await repo.get(persisted_session.id)
        assert entity is not None
        assert entity.id == persisted_session.id

    async def test_get_missing(self, repo: SessionRepository) -> None:
        """Get returns None for a non-existent UUID."""
        entity = await repo.get(uuid.uuid4())
        assert entity is None


class TestList:
    async def test_list_all(self, repo: SessionRepository) -> None:
        """List returns all entities when no filters are applied."""
        await repo.create(AnalysisSession(analysis_type=AnalysisType.REQUIREMENT_ANALYSIS))
        await repo.create(AnalysisSession(analysis_type=AnalysisType.API_TEST_GENERATION))

        items, total = await repo.list()
        assert total == 2
        assert len(items) == 2

    async def test_list_pagination(self, repo: SessionRepository) -> None:
        """List respects page and page_size parameters."""
        for _ in range(5):
            await repo.create(
                AnalysisSession(analysis_type=AnalysisType.REQUIREMENT_ANALYSIS)
            )

        items, total = await repo.list(page=1, page_size=2)
        assert total == 5
        assert len(items) == 2

        items, total = await repo.list(page=3, page_size=2)
        assert total == 5
        assert len(items) == 1

    async def test_list_filters(self, repo: SessionRepository) -> None:
        """List applies equality filters."""
        await repo.create(
            AnalysisSession(
                analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
                title="Req",
            )
        )
        await repo.create(
            AnalysisSession(
                analysis_type=AnalysisType.API_TEST_GENERATION,
                title="API",
            )
        )

        items, total = await repo.list(analysis_type=AnalysisType.REQUIREMENT_ANALYSIS)
        assert total == 1
        assert items[0].title == "Req"


# ── Update ──────────────────────────────────────────────────────


class TestUpdate:
    async def test_update_existing(
        self, repo: SessionRepository, persisted_session: AnalysisSession
    ) -> None:
        """Update modifies fields and returns the updated entity."""
        updated = await repo.update(
            persisted_session.id,
            {"title": "Updated Title"},
        )
        assert updated is not None
        assert updated.title == "Updated Title"

        # Verify persistence by fetching again
        fetched = await repo.get(persisted_session.id)
        assert fetched is not None
        assert fetched.title == "Updated Title"

    async def test_update_missing(self, repo: SessionRepository) -> None:
        """Update returns None for a non-existent UUID."""
        result = await repo.update(uuid.uuid4(), {"title": "Nope"})
        assert result is None

    async def test_update_partial(
        self, repo: SessionRepository, persisted_session: AnalysisSession
    ) -> None:
        """Update only changes provided fields (PATCH semantics)."""
        await repo.update(persisted_session.id, {"title": "New Title"})
        fetched = await repo.get(persisted_session.id)
        assert fetched is not None
        assert fetched.title == "New Title"
        # analysis_type should be unchanged
        assert fetched.analysis_type == persisted_session.analysis_type


# ── Delete ──────────────────────────────────────────────────────


class TestDelete:
    async def test_delete_existing(
        self, repo: SessionRepository, persisted_session: AnalysisSession
    ) -> None:
        """Delete removes the entity and returns True."""
        result = await repo.delete(persisted_session.id)
        assert result is True

        fetched = await repo.get(persisted_session.id)
        assert fetched is None

    async def test_delete_missing(self, repo: SessionRepository) -> None:
        """Delete returns False for a non-existent UUID."""
        result = await repo.delete(uuid.uuid4())
        assert result is False
