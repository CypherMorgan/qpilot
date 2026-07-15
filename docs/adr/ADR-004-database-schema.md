# ADR-004: Database Schema

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-01 |
| **Updated** | 2026-07-02 |
| **Author(s)** | CypherPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

CypherPilot persists data across several categories:
- **Analysis sessions** — the link between inputs and outputs for a single AI analysis request
- **Uploaded artifacts** — requirements documents, OpenAPI specs, failure logs
- **Generated outputs** — test cases, PyTest suites, root-cause analyses
- **Provider call metadata** — which provider, model, token usage, latency, status
- **Future entities** — workspaces, users, prompt versions, export history

The database must support:
- Reliable storage and retrieval of structured analysis data
- JSON fields for flexible AI response data that doesn't fit a fixed schema
- Efficient queries for history listing (sorted by date, filtered by type)
- Migrations that can evolve without downtime (or with minimal downtime for single-user)
- A design that can be extended for multi-user support without a schema overhaul

---

## Problem Statement

Design a PostgreSQL database schema for the CypherPilot MVP that:

1. Supports all three MVP modules with a unified session-based model
2. Stores AI provider call metadata (provider, model, tokens, latency) alongside each analysis
3. Uses JSON for flexible AI response data while keeping queryable fields in structured columns
4. Can be extended for multi-user/auth without a migration apocalypse
5. Follows SQLAlchemy 2.0 best practices (declarative models, typed columns, relationships)

---

## Decision

### Entity-Relationship Diagram

```
┌─────────────────────────────────────────────────────┐
│                  AnalysisSession                      │
│─────────────────────────────────────────────────────│
│ id                (UUID, PK)                          │
│ title             (VARCHAR, nullable)                 │
│ analysis_type     (Enum, not null)                    │
│ │                 ("requirement-analysis",             │
│ │                  "api-test-generation",              │
│ │                  "failure-analysis")                 │
│ status            (Enum, not null)                    │
│ │                 ("pending", "processing",            │
│ │                  "completed", "failed")              │
│                                                       │
│ input_source_type (VARCHAR, nullable)                 │
│ input_content     (TEXT, nullable)                    │
│ input_filename    (VARCHAR, nullable)                 │
│                                                       │
│ output_data       (JSON, nullable)                    │
│ output_format     (VARCHAR, nullable)                 │
│                                                       │
│ provider_used     (VARCHAR, nullable)                 │
│ model_used        (VARCHAR, nullable)                 │
│ prompt_tokens     (INTEGER, nullable)                 │
│ completion_tokens (INTEGER, nullable)                 │
│ total_tokens      (INTEGER, nullable)                 │
│ latency_ms        (INTEGER, nullable)                 │
│                                                       │
│ error_message     (TEXT, nullable)                    │
│ config            (JSON, nullable)                    │
│                                                       │
│ created_at        (TIMESTAMPTZ, not null)             │
│ updated_at        (TIMESTAMPTZ, not null)             │
└─────────────────────────────────────────────────────┘
```

### Table Definition

```sql
CREATE TABLE analysis_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(255),
    analysis_type   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',

    -- Input fields
    input_source_type   VARCHAR(50),
    input_content       TEXT,
    input_filename      VARCHAR(255),

    -- Output fields
    output_data         JSON,
    output_format       VARCHAR(20),

    -- AI provider tracking
    provider_used       VARCHAR(50),
    model_used          VARCHAR(100),
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    total_tokens        INTEGER,
    latency_ms          INTEGER,

    -- Error tracking
    error_message       TEXT,

    -- Config (generic extensibility)
    config              JSON,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sessions_created_at ON analysis_sessions(created_at DESC);
CREATE INDEX idx_sessions_type_status ON analysis_sessions(analysis_type, status);
```

**Why a unified `analysis_sessions` table instead of per-module tables?**
- All modules share the same workflow: receive input → process (with AI) → produce output
- A single table simplifies history listing, sorting, and cross-module queries
- The `analysis_type` discriminator cleanly separates module concerns
- Per-module specific data lives in `output_data` (JSON) — not in session columns

**Why embed provider metadata on the session row instead of a separate table?**
- MVP makes exactly one AI provider call per session — no multi-call sessions yet
- A single row avoids JOINs for the most common query (get session + provider info)
- Simpler code: one repository, one create/update operation per session
- If multi-call sessions are needed in the future, we can add a `provider_calls` table and migrate

**Why `output_data` is JSON (not JSONB)?** SQLite (used in tests) doesn't support JSONB. Using plain `JSON()` keeps the type compatible across both PostgreSQL and SQLite without dialect-specific types. The performance difference is negligible at MVP scale.

### SQLAlchemy ORM Model

```python
# app/infrastructure/models/analysis_session.py

from sqlalchemy import JSON, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models import AnalysisStatus, AnalysisType
from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class InputSourceType(str, Enum):
    """Supported input types for analysis."""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"


class AnalysisSession(Base, UUIDMixin, TimestampMixin):
    """An analysis session — root aggregate of the CypherPilot domain."""

    __tablename__ = "analysis_sessions"

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    analysis_type: Mapped[AnalysisType] = mapped_column(
        Enum(AnalysisType, name="analysis_type_enum", create_constraint=True),
        nullable=False,
    )

    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status_enum", create_constraint=True),
        nullable=False,
        default=AnalysisStatus.PENDING,
    )

    # Input fields
    input_source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_content: Mapped[str | None] = mapped_column(Text(), nullable=True)
    input_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Output fields
    output_data: Mapped[dict | None] = mapped_column(JSON(), nullable=True)
    output_format: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # AI provider tracking
    provider_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer(), nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)

    # Config (generic extensibility)
    config: Mapped[dict | None] = mapped_column(JSON(), nullable=True)
```

---

## Alternatives Considered

### Alternative A: Per-Module Tables (Rejected)

Each module has its own set of tables:

```sql
CREATE TABLE req_analysis_sessions (...);
CREATE TABLE api_test_sessions (...);
CREATE TABLE failure_analysis_sessions (...);
```

| Dimension | Per-Module Tables | Unified Schema (Chosen) |
|---|---|---|
| **Schema isolation** | Complete — modules can't accidentally affect each other | Shared — one migration can affect all modules |
| **Query complexity** | Simple — each table has focused columns | JSON queries can be more complex |
| **Cross-module queries** | Impossible without UNION | Natural — `WHERE analysis_type = '...'` |
| **History listing** | Union across N tables | Single `SELECT * FROM analysis_sessions` |
| **Migration overhead** | N migration chains | One migration chain |
| **Schema rigidity** | Columns for each field are predefined | JSON allows flexible schema per module |

**Decision:** Rejected. Per-module tables would make cross-module queries require UNIONs or application-level joining. The unified schema with JSON gives us the best of both worlds: structured columns for common fields and flexible JSON for module-specific data.

### Alternative B: Document Store (MongoDB) (Rejected)

| Dimension | MongoDB | PostgreSQL + JSON (Chosen) |
|---|---|---|
| **Schema flexibility** | Native — schemaless by design | JSON provides flexible columns within relational tables |
| **Relationships** | Manual — application-level joins | Native — foreign keys, JOINs, cascade deletes |
| **Transactions** | Limited — multi-document transactions are complex | Full ACID — all operations are transactional |
| **Migration** | No migration needed (schemaless) | Alembic-managed migrations |
| **Operations** | Separate DB to manage + learn | Same PostgreSQL for all data |

**Decision:** Rejected. Our data is inherently relational (sessions as root aggregates). PostgreSQL's JSON gives us the schema flexibility we need without sacrificing relational integrity. Running two databases for a single-user MVP is unjustified complexity.

### Alternative C: Normalized 4-Table Schema (Deferred)

A fully normalized design with separate tables for artifacts, generated outputs, and provider calls:

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    ...
);

CREATE TABLE generated_outputs (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    output_type TEXT NOT NULL,
    content JSONB NOT NULL,
    ...
);

CREATE TABLE provider_calls (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    ...
);
```

| Dimension | Normalized 4-Table | Single-Table JSON (Chosen) |
|---|---|---|
| **Queryability** | Good — each entity has its own indexed columns | Adequate — JSON fields for flexible data |
| **Atomic updates** | Update specific row in specific table | Rewrite `output_data` JSON to update one field |
| **Data integrity** | Full relational integrity | No FK constraints on JSON internals |
| **Simplicity** | 4 tables with relationships | 1 table, 1 model, 1 repository |
| **Provider analytics** | Efficient — dedicated table with indexes | Requires scanning JSON fields |
| **Multi-call sessions** | Native support — multiple rows per session | Requires schema migration |

**Decision:** Deferred to post-MVP. The 4-table design is more correct for a production system, but:
1. MVP makes exactly one provider call per session — no multi-call support needed
2. File storage is handled by embedding base64 content in `output_data` JSON rather than filesystem storage
3. A single table dramatically simplifies the initial Alembic migration and repository layer
4. We can add normalized tables when the need arises (multi-call sessions, file storage, provider analytics)

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **Single table** vs **Normalized tables** | One table is simpler to implement and query for MVP. Normalized tables would be better for provider analytics and multi-call sessions, but these aren't needed yet. Migration path: add tables + backfill. |
| **JSON flexibility** vs **Schema rigidity** | JSON for `output_data` means we can evolve output formats without migrations, but we lose compile-time validation. Mitigated by Pydantic validation before persistence — invalid data never reaches the database. |
| **Embedded provider metadata** vs **Separate table** | Embedding avoids JOINs for the common case (get session). A separate table would be needed for per-call tracking in multi-call sessions. |
| **UUID PKs** vs **Auto-increment integers** | UUIDs are larger (16 bytes vs 4 bytes) and slower to index, but they prevent enumeration attacks and simplify future distributed deployment. For a single-user MVP, the performance difference is negligible. |

---

## Consequences

### Positive

1. **Unified session model** — all three MVP modules use the same model, repository, and queries
2. **JSON for flexibility** — module-specific output structures can evolve without schema migrations
3. **Simple repository** — single table means no JOINs, no relationships, one CRUD interface
4. **Workspace-ready** — can add `workspace_id` column as nullable FK for future multi-user support
5. **Full ACID guarantees** — all operations are transactional; partial failures can't leave orphaned data

### Negative

1. **JSON query complexity** — querying into `output_data` requires PostgreSQL JSON operators
2. **No per-output-type validation at the DB level** — validation relies on the application layer (Pydantic)
3. **Provider analytics require scanning** — querying "average latency per provider" requires loading all sessions or a separate migration to a dedicated table

### Neutral

1. **Migrations required for schema changes** — Alembic migrations for column additions/removals, but JSON schema changes don't need migrations

---

## Implementation Impact

### New Files

```
app/infrastructure/
├── __init__.py
├── database.py              # DatabaseManager, get_db, AsyncSession
├── database/
│   ├── __init__.py
│   └── base.py              # Base, TimestampMixin, UUIDMixin
├── models/
│   ├── __init__.py           # Registers models on Base.metadata
│   ├── base.py               # TimestampMixin, UUIDMixin
│   └── analysis_session.py   # AnalysisSession ORM model
└── repository.py             # BaseRepository with generic CRUD
```

### Alembic Setup

```
alembic/
├── alembic.ini
├── env.py
└── versions/
    └── 0001_initial_schema.py
```

### Modified Files

- `pyproject.toml` — add `alembic`, `asyncpg`, `aiosqlite` dependencies
- `.env.example` — add `DATABASE_URL`
- `docker-compose.yml` — PostgreSQL 16 service

### Initial Migration

The first Alembic migration creates the `analysis_sessions` table with all embedded columns.

---

## Testing Impact

### Repository Tests

```python
# tests/infrastructure/database/test_repositories.py

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session


async def test_create_analysis_session(session):
    repo = BaseRepository[AnalysisSession]()
    repo.model_class = AnalysisSession
    created = await repo.create(
        AnalysisSession(
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            status=AnalysisStatus.PENDING,
        )
    )
    assert created.id is not None
    assert created.status == AnalysisStatus.PENDING


async def test_session_with_output(session):
    repo = BaseRepository[AnalysisSession]()
    repo.model_class = AnalysisSession
    created = await repo.create(
        AnalysisSession(
            analysis_type=AnalysisType.API_TEST_GENERATION,
            status=AnalysisStatus.COMPLETED,
            output_data={"spec_title": "Pet Store API", "files": [...]},
            provider_used="openrouter",
            total_tokens=1500,
        )
    )
    assert created.output_data["spec_title"] == "Pet Store API"
```

### What to Test

| Test | Validates |
|---|---|
| Session CRUD | Create, read, list, update sessions |
| Output storage | Store and retrieve generated output data |
| Provider metadata | Log provider, model, tokens, latency |
| Status transitions | `pending → processing → completed/failed` |
| Index performance | Queries use indexes (EXPLAIN ANALYZE) |

---

## Future Evolution

| Phase | Change | Impact |
|---|---|---|
| **Multi-user auth** | Add `workspace_id` column, add `users` table | New column + table, backfill |
| **Provider analytics** | Add `provider_calls` table, migrate existing data | New table, migration of embedded data |
| **File storage** | Add `artifacts` table, migrate base64 content | New table, migration of embedded file data |
| **Multi-call sessions** | Add `provider_calls` table for per-call tracking | New table, session → multiple calls |
| **Soft delete** | Add `deleted_at` column | New column, query filter |
| **Export history** | Add `exports` table referencing sessions | New table |
| **Analytics** | Add materialized views for provider metrics | New views, refresh schedule |

---

## Decision Rationale Summary

The Database Schema is **justified** because:

1. **It solves a real problem** — without a schema, data would be stored in ad-hoc files or in-memory structures
2. **The cost is minimal** — one table, one Alembic migration, one ORM model
3. **The value is immediate** — every MVP module needs to persist and retrieve analysis data
4. **It demonstrates engineering maturity** — unified session model with JSON flexibility, proper indexing strategy, future-proofed for multi-user

**Abstraction question answers (per engineering rule):**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Structured persistence for all analysis data — inputs, outputs, provider metadata |
| **Why is this necessary today?** | Every MVP module creates, reads, and lists analysis data |
| **What simpler alternative exists?** | File-based storage (JSON on disk per session) |
| **Why was that rejected?** | No querying, no atomic updates, no rollback — file-based storage would need to be replaced before the first feature shipped |
| **How does this help evolution?** | Single-table schema is trivially extensible; adding columns or normalized tables does not require a rewrite |
