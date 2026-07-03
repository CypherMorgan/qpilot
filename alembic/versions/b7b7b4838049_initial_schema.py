"""initial_schema

Creates:

- ``analysis_status_enum`` — ENUM for session lifecycle states
- ``analysis_type_enum``   — ENUM for supported analysis types
- ``analysis_sessions``    — Root entity: every AI analysis is a session

Schema matches ``app.infrastructure.models.analysis_session.AnalysisSession``
(ADR-004).

Uses raw SQL with ``IF NOT EXISTS`` / ``DO $$ ... EXCEPTION`` guards so the
migration is fully idempotent across container restarts.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7b7b4838049"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial schema."""
    # ── ENUM types (idempotent via DO $$ ... EXCEPTION) ──────
    op.execute(
        """\
        DO $$
        BEGIN
            CREATE TYPE analysis_status_enum AS ENUM (
                'pending', 'processing', 'completed', 'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.execute(
        """\
        DO $$
        BEGIN
            CREATE TYPE analysis_type_enum AS ENUM (
                'requirement-analysis',
                'api-test-generation',
                'failure-analysis'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    # ── Table (idempotent via IF NOT EXISTS) ──────────────────
    op.execute(
        """\
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title       VARCHAR(255),
            analysis_type analysis_type_enum NOT NULL,
            status      analysis_status_enum NOT NULL DEFAULT 'pending',
            config      JSONB,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    """Revert the initial schema."""
    op.execute("DROP TABLE IF EXISTS analysis_sessions CASCADE")
    op.execute("DROP TYPE IF EXISTS analysis_type_enum")
    op.execute("DROP TYPE IF EXISTS analysis_status_enum")
