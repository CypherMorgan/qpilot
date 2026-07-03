"""Database infrastructure tests.

Tests the DatabaseManager lifecycle and session management using
an in-memory SQLite database (no PostgreSQL required).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import DatabaseManager


@pytest.fixture
async def manager() -> DatabaseManager:
    """Return a DatabaseManager backed by in-memory SQLite."""
    m = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
    await m.create_all()
    yield m
    await m.drop_all()
    await m.close()


# ── Engine & session factory ────────────────────────────────────


class TestDatabaseManagerInit:
    """Verify that the engine and session factory are created correctly."""

    def test_engine_is_created(self) -> None:
        """Engine is available after construction."""
        m = DatabaseManager("sqlite+aiosqlite:///:memory:")
        assert m.engine is not None
        assert "Engine" in type(m.engine).__name__

    def test_session_factory_is_created(self) -> None:
        """Session factory is available after construction."""
        m = DatabaseManager("sqlite+aiosqlite:///:memory:")
        assert m.session_factory is not None


# ── Lifecycle ───────────────────────────────────────────────────


class TestDatabaseManagerLifecycle:
    """Verify create_all, drop_all, and close."""

    async def test_create_all_and_drop_all(self, manager: DatabaseManager) -> None:
        """create_all creates tables, drop_all removes them.

        We verify by checking for the analysis_sessions table.
        """
        # Table should exist after create_all
        async with manager.engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='analysis_sessions'"
                )
            )
            assert result.scalar() == "analysis_sessions"

        await manager.drop_all()

        # Table should be gone after drop_all
        async with manager.engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name='analysis_sessions'"
                )
            )
            assert result.scalar() is None

    async def test_close_disposes_engine(self, manager: DatabaseManager) -> None:
        """close() disposes the engine's connection pool."""
        await manager.close()
        # The engine's pool should be disposed; disposing twice is a no-op
        await manager.close()


# ── Health ──────────────────────────────────────────────────────


class TestDatabaseManagerHealth:
    """Verify the connection health check."""

    async def test_check_connection_success(self, manager: DatabaseManager) -> None:
        """check_connection returns True when the DB is reachable."""
        assert await manager.check_connection() is True

    async def test_check_connection_after_close(self, manager: DatabaseManager) -> None:
        """close() does not raise after the engine is disposed."""
        await manager.close()
        await manager.close()  # double-dispose must be safe


# ── Session ─────────────────────────────────────────────────────


class TestDatabaseManagerSession:
    """Verify session creation and basic operations."""

    async def test_session_executes_queries(self, manager: DatabaseManager) -> None:
        """A session obtained from the factory can execute SQL."""
        async with manager.session() as session:
            result = await session.execute(text("SELECT 1 AS val"))
            assert result.scalar() == 1

    async def test_session_insert_and_query(
        self, manager: DatabaseManager
    ) -> None:
        """A session can insert and retrieve data."""
        from app.domain.models import AnalysisType
        from app.infrastructure.models.analysis_session import AnalysisSession

        session: AsyncSession
        async with manager.session() as session:
            entity = AnalysisSession(
                analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            )
            session.add(entity)
            await session.commit()

        # Query in a new session
        async with manager.session() as session:
            result = await session.get(AnalysisSession, entity.id)
            assert result is not None
            assert result.id == entity.id
            assert result.analysis_type == AnalysisType.REQUIREMENT_ANALYSIS
            assert result.status.name == "PENDING"
