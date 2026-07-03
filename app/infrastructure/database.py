"""Database engine, session management, and async session dependency.

Architecture
------------
  DatabaseManager wraps an async SQLAlchemy engine and session factory.
  It is initialised during the application lifespan and stored on
  ``app.state.db_manager``.  FastAPI route handlers obtain a database
  session via the ``get_db`` dependency.

Testability
-----------
  Override ``DATABASE_URL`` to ``sqlite+aiosqlite:///:memory:`` in tests.
  The same code path works with both PostgreSQL and SQLite, so repository
  logic can be verified without a live database server.

  Use ``db_manager.create_all()`` / ``drop_all()`` to set up and tear
  down tables in test fixtures.

Future evolution
----------------
  - Read replicas: create a second ``DatabaseManager`` with a read-only
    URL and inject via a separate dependency.
  - Connection pooling: tuned through ``DatabaseConfig.pool_size`` and
    ``max_overflow``.
  - Driver swap: changing ``postgresql+asyncpg://`` → ``postgresql+psycopg://``
    requires no code changes beyond the URL.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from structlog import get_logger

_logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all database models.

    Every ORM model inherits from this class.  SQLAlchemy 2.0 style —
    use ``Mapped`` / ``mapped_column`` for column definitions.
    """


class DatabaseManager:
    """Manages the async database engine and session factory lifecycle.

    Usage::

        manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
        async with manager.session() as session:
            session.add(my_model)
            await session.commit()

    Create/drop all tables (suitable for tests or migrations-free dev)::

        await manager.create_all()
        await manager.drop_all()
    """

    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._engine = create_async_engine(database_url, echo=echo)
        self._session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        )

    # ── Properties ──────────────────────────────────────────────

    @property
    def engine(self) -> AsyncEngine:
        """The underlying :class:`sqlalchemy.ext.asyncio.AsyncEngine`."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """The :class:`sqlalchemy.ext.asyncio.async_sessionmaker` instance."""
        return self._session_factory

    # ── Lifecycle ───────────────────────────────────────────────

    async def close(self) -> None:
        """Dispose of the connection pool and release all resources.

        Call during application shutdown (lifespan teardown).
        """
        if self._engine is None:
            return
        await self._engine.dispose()
        _logger.debug("Database engine disposed")

    async def create_all(self) -> None:
        """Create all tables defined by models that import ``Base``.

        Intended for testing and local development.  Production should
        use Alembic migrations instead.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _logger.debug("All database tables created")

    async def drop_all(self) -> None:
        """Drop all tables.

        Intended for testing.  Use with extreme caution in production.
        """
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        _logger.debug("All database tables dropped")

    # ── Health ──────────────────────────────────────────────────

    async def check_connection(self) -> bool:
        """Return ``True`` if the database is reachable."""
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            _logger.warning("Database health check failed", exc_info=True)
            return False

    # ── Session helpers ─────────────────────────────────────────

    def session(self) -> AsyncSession:
        """Open a new :class:`AsyncSession` (use as a context manager).

        Example::

            async with manager.session() as session:
                ...
        """
        return self._session_factory()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage in route handlers::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(MyModel))

    The session is obtained from the ``DatabaseManager`` stored at
    ``request.app.state.db_manager`` (set during the lifespan startup).
    It is automatically closed when the request completes.

    The **Request** parameter is injected by FastAPI into the dependency
    even when the endpoint does not declare it — this is the standard
    FastAPI pattern for accessing application state.
    """
    manager: DatabaseManager = request.app.state.db_manager
    async with manager.session() as session:
        yield session
