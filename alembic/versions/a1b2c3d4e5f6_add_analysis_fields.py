"""add_analysis_fields

Adds input, output, AI provider tracking, and error fields to the
``analysis_sessions`` table for Phase 3 — Requirement Analysis.

New columns (all nullable for backward compatibility):

- ``input_source_type``   VARCHAR(50)
- ``input_content``       TEXT
- ``input_filename``      VARCHAR(255)
- ``output_data``         JSONB
- ``output_format``       VARCHAR(20)
- ``provider_used``       VARCHAR(50)
- ``model_used``          VARCHAR(100)
- ``prompt_tokens``       INTEGER
- ``completion_tokens``   INTEGER
- ``total_tokens``        INTEGER
- ``latency_ms``          INTEGER
- ``error_message``       TEXT

Revision ID: a1b2c3d4e5f6
Revises: b7b7b4838049
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "b7b7b4838049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add new columns to analysis_sessions table."""
    op.execute(
        """\
        ALTER TABLE analysis_sessions
            ADD COLUMN IF NOT EXISTS input_source_type VARCHAR(50),
            ADD COLUMN IF NOT EXISTS input_content TEXT,
            ADD COLUMN IF NOT EXISTS input_filename VARCHAR(255),
            ADD COLUMN IF NOT EXISTS output_data JSONB,
            ADD COLUMN IF NOT EXISTS output_format VARCHAR(20),
            ADD COLUMN IF NOT EXISTS provider_used VARCHAR(50),
            ADD COLUMN IF NOT EXISTS model_used VARCHAR(100),
            ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER,
            ADD COLUMN IF NOT EXISTS completion_tokens INTEGER,
            ADD COLUMN IF NOT EXISTS total_tokens INTEGER,
            ADD COLUMN IF NOT EXISTS latency_ms INTEGER,
            ADD COLUMN IF NOT EXISTS error_message TEXT
        """
    )


def downgrade() -> None:
    """Remove the columns added in this migration."""
    op.execute(
        """\
        ALTER TABLE analysis_sessions
            DROP COLUMN IF EXISTS input_source_type,
            DROP COLUMN IF EXISTS input_content,
            DROP COLUMN IF EXISTS input_filename,
            DROP COLUMN IF EXISTS output_data,
            DROP COLUMN IF EXISTS output_format,
            DROP COLUMN IF EXISTS provider_used,
            DROP COLUMN IF EXISTS model_used,
            DROP COLUMN IF EXISTS prompt_tokens,
            DROP COLUMN IF EXISTS completion_tokens,
            DROP COLUMN IF EXISTS total_tokens,
            DROP COLUMN IF EXISTS latency_ms,
            DROP COLUMN IF EXISTS error_message
        """
    )
