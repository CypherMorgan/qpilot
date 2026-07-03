"""Shared model base classes and mixins.

Provides:

* ``Base`` — declarative base for all ORM models (re-exported from
  ``app.infrastructure.database`` for convenience).
* ``TimestampMixin`` — adds ``created_at`` and ``updated_at`` columns
  with server defaults.
* ``UUIDMixin`` — adds a UUID primary key column ``id``.

Design decision: mixin classes rather than a single ``BaseModel`` base
so that future models can select which columns they need without
inheriting unwanted fields.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Adds a UUID primary key column ``id``.

    Uses ``sqlalchemy.Uuid`` which renders as native UUID on PostgreSQL
    and as VARCHAR / BLOB on other backends (SQLite), making tests
    portable without a PostgreSQL server.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` timestamp columns.

    Both columns use ``DateTime(timezone=True)`` (TIMESTAMPTZ on
    PostgreSQL) with server-side ``now()`` defaults.

    ``updated_at`` is automatically refreshed by the database on every
    UPDATE via ``onupdate=func.now()``.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
