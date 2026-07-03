"""Generic repository with common CRUD operations.

Architecture
------------
  ``BaseRepository[T]`` is a generic repository that provides the
  standard persistence operations (create, get, list, update, delete)
  for any SQLAlchemy model.

  Subclasses set ``model_class`` to the ORM model and inherit all
  CRUD methods.  Custom query methods are added in subclasses.

  Example::

      class AnalysisSessionRepository(BaseRepository[AnalysisSession]):
          model_class = AnalysisSession

          async def find_pending(self) -> list[AnalysisSession]:
              stmt = select(self.model_class).where(...)
              result = await self._session.execute(stmt)
              return list(result.scalars().all())

Testability
-----------
  Repositories depend only on ``AsyncSession``, not on engine or config.
  In tests, pass a session bound to an in-memory SQLite database.
  No mocking required — just create the test database and inject the
  session.

Future evolution
----------------
  - Soft-delete support via a ``deleted_at`` mixin and ``only_active()``
    filter in the repository.
  - Caching layer can wrap repository methods transparently.
  - Read-only replicas can be injected as a separate ``AsyncSession``
    for read-heavy endpoints.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select as _Select

from app.infrastructure.database import Base

Select = _Select[tuple[Any]]
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository providing standard CRUD operations.

    Subclasses **must** define ``model_class`` to bind to a specific
    ORM model::

        class SessionRepo(BaseRepository[AnalysisSession]):
            model_class = AnalysisSession
    """

    model_class: type[T]
    """The ORM model class this repository manages."""

    default_page_size: int = 20
    max_page_size: int = 100

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Create ──────────────────────────────────────────────────

    async def create(self, model: T) -> T:
        """Persist a new model instance and return it with an ID."""
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    # ── Read ────────────────────────────────────────────────────

    async def get(self, id_: UUID) -> T | None:
        """Retrieve a single instance by UUID primary key."""
        return await self._session.get(self.model_class, id_)

    async def list(
        self,
        *,
        page: int = 1,
        page_size: int | None = None,
        order_by: str | None = None,
        ascending: bool = True,
        **filters: Any,
    ) -> tuple[list[T], int]:
        """Return a paginated, filtered list of instances.

        Args:
            page: 1-indexed page number.
            page_size: Items per page (default ``default_page_size``).
            order_by: Column name to order by (e.g. ``"created_at"``).
            ascending: Sort ascending when True, descending when False.
            **filters: Keyword arguments matching column names.

        Returns:
            Tuple of ``(items, total_count)``.
        """
        page_size = min(
            page_size or self.default_page_size,
            self.max_page_size,
        )

        # Build a SELECT query with optional filters
        stmt = select(self.model_class)

        for col_name, value in filters.items():
            column = getattr(self.model_class, col_name, None)
            if column is not None:
                stmt = stmt.where(column == value)

        # Count total matching rows
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = await self._session.scalar(count_stmt) or 0

        # Ordering
        if order_by is not None:
            order_col = getattr(self.model_class, order_by, None)
            if order_col is not None:
                stmt = stmt.order_by(order_col.asc() if ascending else order_col.desc())

        if page_size > 0:
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ── Update ──────────────────────────────────────────────────

    async def update(self, id_: UUID, data: dict[str, Any]) -> T | None:
        """Partially update an instance (PATCH semantics).

        Only the keys provided in ``data`` are changed.  Returns the
        updated instance or ``None`` if not found.
        """
        model = await self.get(id_)
        if model is None:
            return None

        for field, value in data.items():
            if hasattr(model, field):
                setattr(model, field, value)

        await self._session.commit()
        await self._session.refresh(model)
        return model

    # ── Delete ──────────────────────────────────────────────────

    async def delete(self, id_: UUID) -> bool:
        """Delete an instance by UUID.  Returns ``True`` if deleted."""
        model = await self.get(id_)
        if model is None:
            return False

        await self._session.delete(model)
        await self._session.commit()
        return True

    # ── Internal helpers ────────────────────────────────────────

    def _apply_filters(self, stmt: Select, **filters: Any) -> Select:
        """Apply equality filters from keyword arguments to a SELECT.

        Silently skips keys that don't correspond to model columns.
        """
        for col_name, value in filters.items():
            column = getattr(self.model_class, col_name, None)
            if column is not None:
                stmt = stmt.where(column == value)
        return stmt
