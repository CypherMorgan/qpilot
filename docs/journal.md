# QPilot — Engineering Journal

> A running record of architectural decisions, lessons learned, and engineering rationale throughout the project lifecycle.

---

## 2026-07-01 — Project Inception

### What we did
- Formally initiated the QPilot project
- Established development philosophy: design-first, implement-second, with architectural review before every major phase
- Defined engineering principles: Clean Architecture, SOLID, separation of concerns, feature-first modularity, strong typing
- Completed Phase 0 — Product Discovery

### Key decisions made
1. **Renamed from "Cyp QPilot" to "QPilot"** — the original name implied Cypress-specific tooling, which contradicted our framework-agnostic vision. QPilot = Quality Pilot.
2. **Single-user, self-hosted web app** for MVP — no auth, no multi-tenancy, no SaaS. Keeps scope tight.
3. **Artifact-driven over chat-driven** — users upload files, get structured outputs. AI is the engine, not the interface.
4. **Module independence** — Requirement Analysis, API Test Generation, and Automation Failure Analysis are independent modules sharing only platform infrastructure.
5. **Google Gemini as primary MVP provider** — generous free tier enables development without paid subscriptions. Provider abstraction designed for easy extension.
6. **No caching, no CLI, no test execution, no real-time features** in MVP — documented as explicit non-goals.

### Lessons learned
- The act of writing non-goals was as valuable as writing the vision — it forced explicit trade-off acknowledgment.
- Defining success criteria before architecture prevents "good enough" from being accepted as "done."

### Next steps
- Begin Phase 1 — System Design
- Produce architecture diagrams, ADRs, database design, API contracts, and AI orchestration design
- Review every design decision before implementation

---

## 2026-07-01 — C4 Diagrams (Levels 1 & 2)

### What we did
- Produced C4 Context Diagram (Level 1) — defined system boundary, users, external systems
- Updated to include Ollama as a future AI provider alongside Gemini
- Produced C4 Container Diagram (Level 2) — defined three-container architecture (Frontend, API, Database)
- Established Container Interaction Rules (4 hard rules governing cross-container communication)

### Key decisions made
1. **Three-container architecture** — React SPA, FastAPI API, PostgreSQL. Future containers (Redis, workers, object storage) added only when needed.
2. **Frontend stack** — React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + React Router + TanStack Query. No global state library unless needed.
3. **FastAPI over Django/Flask** — async-native, Pydantic-native, auto-docs. Best fit for API-first AI platform.
4. **Frontend serves static files via Nginx** in production, Vite dev server in development. Backend does not serve frontend.
5. **All AI traffic is server-mediated** — browser never calls AI providers directly.

### Engineering rules added
- Business modules → AI Orchestrator → Provider Abstraction (never direct)
- No cross-module access to internal implementations
- Infrastructure depends on abstractions, not concretions
- Shared code kept minimal; module-private code stays in module
- Simplicity first; complexity requires explicit justification
- Testability is a first-class design concern — every component must be mockable at its boundary

---

## 2026-07-01 — C4 Component Diagram (Level 3) + Architecture Categories

### What we did
- Produced C4 Component Diagram (Level 3) — opened the API Application container to reveal 16 internal components
- Defined 4 architectural categories: Presentation, Application, Domain, Infrastructure
- Mapped every component to exactly one category with classification rules
- Established the "Category Boundary Rule": Presentation → Application → Domain, with Infrastructure implementing interfaces

### Key decisions made
1. **AI Orchestrator as the single gateway** — no feature module touches an AI provider directly. All AI interactions flow through one component.
2. **Repository pattern applied pragmatically** — only for aggregates that need persistence (AnalysisSession, Artifact). No repositories for config, prompts, or logging.
3. **Manual DI wiring at startup** — no auto-discovery, no reflection, no hidden containers. Every dependency is visible in startup code.
4. **Component categories formalized** — every component belongs to exactly one of Presentation/Application/Domain/Infrastructure.
5. **New abstraction rule** — before introducing any abstraction, answer: What problem does it solve? Why today? What simpler alternative exists? Why was it rejected? How does it help evolution/testing?

### Lessons learned
- The four-category classification forced clean-up of several ambiguous components. For example, the Prompt Manager was initially unclear — is it domain (prompt content) or infrastructure (file loading)? Answer: the *templates* are domain content, the *manager* that loads/render them is infrastructure.
- "Repository for everything" would have been over-engineering. Restricting repositories to persisted aggregates keeps the pattern meaningful.

### Next steps
- ✅ Produce ADR-001: Provider Abstraction
- ✅ Produce ADR-002: Prompt Management
- ✅ Produce ADR-003: Module Architecture
- ✅ Produce ADR-004: Database Schema
- ✅ Produce ADR-005: API Design
- Move to Phase 2: Engineering Foundation

---

## 2026-07-01 — Architecture Decision Records (ADRs 001-005)

### What we did
- Produced 5 Architecture Decision Records covering every major architectural decision

### ADR-001: Provider Abstraction
- Defined `BaseProvider` as a `typing.Protocol` (structural subtyping, not ABC)
- Defined `PromptRequest` (input) and `ProviderResponse` (output) models
- `ProviderRegistry` maps provider names to adapter instances
- AI Orchestrator depends on Provider Interface, not on any specific provider
- GeminiProvider is the MVP adapter; Claude, OpenAI, Ollama are one adapter class each
- **Key decision:** Protocol over ABC — structural typing is more Pythonic and creates looser coupling

### ADR-002: Prompt Management
- Prompts are versioned Markdown files in a dedicated `prompts/` directory
- `PromptManager` loads, caches, and renders templates using Jinja2
- Template directory: `prompts/analysis/{analysis_type}/{version}/system.md`
- Explicit version selection (e.g., `"v1"`) — no implicit "latest" alias
- **Key decision:** Filesystem over database — git-native versioning, PR-reviewable, simpler MVP

### ADR-003: Module Architecture
- Each feature module is an independent Python package: `app/modules/{module_name}/`
- Standard structure: `router.py`, `service.py`, `models.py`, `prompts/`, `repository.py`, `tests/`
- Hard rules: no module imports another module's internals; all AI goes through AI Orchestrator
- Explicit module registration in `main.py` — no auto-discovery
- **Key decision:** Module independence over monolithic service — allows parallel development and testing

### ADR-004: Database Schema
- 4 tables: `analysis_sessions`, `artifacts`, `generated_outputs`, `provider_calls`
- Unified session model with `analysis_type` discriminator (not per-module tables)
- JSONB for flexible output content; structured columns for queryable metadata
- `workspace_id` nullable FK for future multi-user support without migration
- **Key decision:** Normalized relational tables over single JSONB blob — enables analytics queries

### ADR-005: API Design
- RESTful, versioned (`/api/v1/`), per-module endpoints
- Consistent response envelope: `{ data: ..., meta: { request_id, timestamp } }`
- Consistent error envelope: `{ error: { code, message, detail }, meta: {...} }`
- Pagination: 1-indexed, 20 default, max 100, `-field` descending sort
- File downloads via ZIP archive for generated Python tests
- **Key decision:** REST over GraphQL — simpler, more standard, sufficient for single-client SPA

---

## 2026-07-01 — Phase 2.1: Python Backend Foundation

### What we did
- Created the FastAPI application scaffold with `create_app()` factory pattern
- Implemented pydantic-settings configuration hierarchy (AppConfig → DatabaseConfig, AIConfig, StorageConfig)
- Defined QPilotError exception hierarchy with error code mapping
- Configured structlog for structured JSON logging (dev/production auto-detection)
- Implemented RequestIDMiddleware for request tracing via `X-Request-ID` header
- Registered 5 hierarchical error handlers (ValidationError, NotFoundError, ProviderError, ConfigurationError, generic)
- Created `GET /api/v1/health` endpoint with response envelope pattern
- Wrote 8 passing tests (5 config + 3 health)

### Key decisions made
1. **Middleware registered in `create_app()` not lifespan** — Adding middleware inside `lifespan()` triggers FastAPI's middleware_stack build before the app is ready. Moved to `create_app()`.
2. **Test env vars at module level** — `os.environ.setdefault(...)` must run before `from app.main import create_app` (which triggers module-level `app = create_app()`). Fixtures are too late.
3. **`response.headers[...]` over `MutableHeaders`** — Direct header assignment works correctly with Starlette's response objects. `MutableHeaders` was an unnecessary abstraction.

### Issues resolved
- `ScopeMismatch` in pytest-asyncio (fixture event loop) — root cause was the env var ordering issue, not loop scope.
- `Cannot add middleware after application has started` — middleware moved out of lifespan.

---

## 2026-07-01 — Phase 2.2: Database & Migration Setup

### What we did
- Created `app/infrastructure/` layer with `DatabaseManager` class wrapping async SQLAlchemy engine lifecycle
- Defined `Base` (declarative base), `UUIDMixin` (UUID PK), `TimestampMixin` (created_at/updated_at) mixins
- Created `AnalysisSession` ORM model matching ADR-004 schema
- Implemented `BaseRepository[T]` generic with full CRUD (create, get, list with pagination/filters, update with PATCH semantics, delete)
- Wired `DatabaseManager` into application lifespan (init on startup, dispose on shutdown)
- Updated `GET /api/v1/health` to report database connectivity check
- Set up Alembic with async support (env.py with `run_sync`), initial migration for `analysis_sessions` table
- 29 passing tests (5 config, 7 database, 3 health, 14 repository)

### Key decisions made
1. **`Field(default_factory=DatabaseConfig)`** — pydantic-settings evaluates `DatabaseConfig() = DatabaseConfig()` at **class definition time**, freezing env vars at import. `default_factory` defers construction to instance time, enabling `monkeypatch` to work correctly.
2. **SQLite in tests, PostgreSQL in production** — `DATABASE_URL=sqlite+aiosqlite:///:memory:` override in conftest. All types (`Uuid`, `JSON`, `DateTime(timezone=True)`) are cross-backend compatible.
3. **`DatabaseManager` class over module-level functions** — Encapsulates engine and session factory lifecycle cleanly. One instance per app, stored on `app.state.db_manager`.
4. **Manual migration over autogenerate** — The initial migration was written by hand because autogenerate requires a live PostgreSQL instance. Future migrations can use autogenerate when running against the Docker Compose database.

### Issues resolved
- pydantic-settings `Field(default_factory=...)` — nested config fields using `DatabaseConfig()` at the class level freeze env vars at module import time, making pytest's `monkeypatch` ineffective. Fixed with `default_factory`.

---

## 2026-07-01 — Phase 2.3: Docker & Local Development

### What we did
- Created multi-stage `Dockerfile` (builder + runtime, python:3.12-slim, non-root user)
- Created `docker-compose.yml` with PostgreSQL 16 + backend services, health checks, named volumes, internal network
- Created `docker-compose.override.yml` for development (code mount, `--reload`, `.env` loading)
- Created `docker-entrypoint.sh` that runs `alembic upgrade head` before starting uvicorn
- Created `.env.example` with documented configuration
- Created `.dockerignore` to exclude cache, secrets, and build artifacts
- Created `docs/development.md` with onboarding, workflow, troubleshooting, and production guidance
- Built and verified: backend connects to PostgreSQL, Alembic migrations execute, health endpoint reports DB connectivity

### Key decisions made
1. **`python:3.12-slim` base** — 120 MB vs 340 MB for full image. All native dependencies (asyncpg) ship pre-compiled wheels.
2. **Multi-stage build** — Builder installs gcc for native compilation; runtime stage is clean. Smaller attack surface, smaller image.
3. **Shell entrypoint with `exec`** — Migrations run on every startup (`alembic upgrade head` is idempotent). `exec "$@"` replaces shell with uvicorn so signals (SIGTERM) propagate correctly.
4. **Separate override file** — Docker Compose auto-loads `docker-compose.override.yml`. Keeps base config production-safe while enabling dev features without special commands.
5. **No frontend container yet** — Deferred to Phase 2.5 per the roadmap.

### Architecture validation
All ADRs remain valid. The Docker/Compose configuration is a deployment concern orthogonal to the architecture defined in ADR-001 through ADR-005.

---

## 2026-07-02 — Phase 2.4: AI Infrastructure Layer

### What we did
- **Changed default AI provider from Gemini to OpenRouter** — OpenAI-compatible API, free-tier models, no age verification, single access to multiple models. Gemini remains a supported future provider.
- **Built provider-agnostic AI infrastructure** under `app/ai/`:
  - `models.py` — `AIRequest`, `AIResponse`, `TokenUsage`, `ProviderMetadata` domain models
  - `protocol.py` — `AIProvider` as a `typing.Protocol` (structural subtyping)
  - `registry.py` — `ProviderRegistry` with registration, retrieval, duplicate detection
  - `response_validator.py` — JSON parsing, code fence stripping, Pydantic validation
  - `prompt_manager.py` — `PromptManager` with Jinja2 rendering, filesystem caching, strict undefined checking
- **Implemented OpenRouterProvider** — uses httpx, supports authentication, rate limiting, timeout, structured response parsing
- **Implemented OllamaProvider** — validates the abstraction genuinely works with a second adapter. Connection refused, timeout, and HTTP error handling
- **Updated `AIConfig`** — added OpenRouter fields, updated provider lists, improved per-provider validation
- **Updated `exceptions.py`** — added `ProviderUnavailableError`, `AuthenticationError`, `RateLimitError`, `InvalidResponseError`, `InvalidPromptError`
- **Updated `main.py`** — provider registry initialized in lifespan, providers registered conditionally
- **Updated all docs** — ADR-001, ADR-002, vision.md, mvp-scope.md, .env.example, README
- **Removed `google-generativeai` dependency** — no SDKs leak into infrastructure
- **83 passing tests** — 54 new AI infra tests + 29 original tests all pass

### Architecture validation
- **ADR-001** ✅ Fully conforms — Protocol-based interface, registry, provider adapters. Updated models and default provider per implementation.
- **ADR-002** ✅ Fully conforms — PromptManager with Jinja2, caching, strict undefined checking. Templates in `prompts/`.
- **ADR-003** ✅ No impact — Platform code, not a module.
- **ADR-004** ✅ No impact — No schema changes.
- **ADR-005** ✅ No impact — No new API endpoints.

### Lessons learned
- `httpx.MockTransport` is a powerful testing tool — intercepts HTTP at transport level without needing `responses` or `pytest-httpx`.
- Pydantic models with `type[BaseModel]` fields need `arbitrary_types_allowed = True` and `Field(exclude=True)` for serialization.
- `pytest` collects `Test`-prefixed classes as test classes — Pydantic model test classes should use a `_` prefix.

---

## 2026-07-02 — Phase 2.5: Frontend Foundation

### What we did
- **Created ADR-006 (Frontend Architecture)** — design-first document covering tech stack, folder structure, routing strategy, state management, theme system, API client architecture, testing strategy, and Docker integration
- **Scaffolded Vite + React 18 + TypeScript project** in `frontend/` with full dependency set:
  - **Routing**: React Router v6 with nested routes under RootLayout
  - **Server state**: TanStack Query v5 with devtools
  - **HTTP client**: Axios with request/response interceptors, error normalization
  - **UI**: shadcn/ui components (Button, Separator, ScrollArea, Sheet, DropdownMenu, Tooltip)
  - **Icons**: Lucide React
  - **Forms**: React Hook Form + Zod (dependencies installed for Phase 3)
  - **CSS**: Tailwind CSS 3 with class-based dark mode, shadcn/ui CSS variables
- **Built feature-first folder structure** — `src/app/` (infrastructure), `src/modules/` (feature modules, empty for Phase 3), `src/services/` (typed API layer), `src/layouts/` (application shell)
- **Implemented application shell:**
  - **Sidebar** — collapsible navigation with main nav, module nav (disabled/coming-soon), settings. Desktop always visible, mobile via Sheet/drawer. Tooltips for collapsed state.
  - **Topbar** — mobile menu toggle, backend connection indicator (green/red dot), theme toggle
  - **RootLayout** — sidebar + topbar + scrollable `<Outlet />` content area. Responsive: sidebar is hidden on mobile, shown via Sheet.
- **Theme system** — React Context + localStorage persistence + `prefers-color-scheme` initial detection + Tailwind `class` strategy
- **API layer:**
  - `api-client.ts` — Axios instance with 60s timeout, request interceptor, error normalization interceptor
  - `health.ts` — typed service function for health endpoint
  - Error normalization: backend error responses, timeout, network errors, unknown errors all produce a standard `ApiError` shape
- **Pages:**
  - **Home/Dashboard** — health status cards, module cards (coming soon)
  - **Settings** — appearance (light/dark), about section
  - **NotFound** — 404 page with navigation back to dashboard
- **Shared components:**
  - `ErrorBoundary` — class-based React error boundary with retry button
  - `LoadingState` — spinner with optional message, size variants, full-page mode
  - `EmptyState` — icon + title + description + optional action, dashed border container
  - `ThemeToggle` — sun/moon icon button with tooltip
- **Testing infrastructure:**
  - Vitest + React Testing Library + jsdom
  - `test-utils.tsx` — custom `renderWithProviders` wrapping QueryClient + MemoryRouter + ThemeProvider + TooltipProvider
  - `tests/setup.ts` — localStorage + matchMedia mocks for jsdom
  - 17 passing tests (6 files): router, error-boundary, loading-state, api-client, use-theme, use-health
- **Docker integration:**
  - `frontend/Dockerfile` — multi-stage: build with Node 20 Alpine, serve with Nginx Alpine. SPA fallback, API proxy, gzip, long asset cache
  - `frontend/nginx.conf` — 80→backend:8000 API proxy with 120s timeout, SPA fallback, static asset caching, hidden file denial
  - `docker-compose.yml` — added `frontend` service on port 3000, depends on backend
  - `docker-compose.override.yml` — frontend dev notes (use Vite dev server for HMR)
  - Updated CORS origins to include `http://localhost:3000`
- **Documentation updated:**
  - `docs/development.md` — quick start updated for full stack, frontend dev section, project structure updated
  - `docs/adr/ADR-006-frontend-architecture.md` — new ADR covering all architecture decisions
  - `docs/journal.md` — this entry

### Key decisions made
1. **Feature-first modules over pages-first** — `src/modules/` mirrors backend `app/modules/`. Each module is a self-contained directory with its own components, hooks, pages, and types. App-level pages (home, settings, 404) live in `src/app/pages/`.
2. **TanStack Query + local state, no global state library** — Server state caching, refetching, and pagination are handled by TanStack Query. UI toggles and form state stay in local React state or context. Redux/Zustand/MobX explicitly rejected until a genuine need emerges.
3. **shadcn/ui copy-paste over npm dependency** — Full control over each component's styling, no locked-in version, aligned with "production-quality, not production-dependent" philosophy.
4. **Nginx serves the production SPA** — Multi-stage Dockerfile (node:20-alpine build → nginx:alpine runtime). Nginx handles SPA fallback (`try_files $uri /index.html`), API proxy to backend, gzip, and static asset caching.
5. **Vite dev server for development** — HMR at `localhost:5173`. Backend CORS already configured for this origin. Separate from the Docker Compose Nginx container.
6. **`localStorage` + `prefers-color-scheme` for theme** — Persisted preference with OS-level fallback. Simple, no runtime CSS-in-JS, no extra dependencies.
7. **Axios error normalization** — Backend error responses, timeouts, network errors all produce a standard `ApiError` shape. Business modules never deal with raw Axios errors.

### Architecture validation
- **ADR-001** ✅ No impact — Frontend doesn't touch provider abstraction.
- **ADR-002** ✅ No impact — Frontend doesn't handle prompt management.
- **ADR-003** ✅ No impact — Backend module architecture unchanged.
- **ADR-004** ✅ No impact — No schema changes.
- **ADR-005** ✅ No impact — Health endpoint integration uses existing `/api/v1/health` contract.
- **ADR-006** ✅ (New) Frontend architecture documented and implemented as designed. Feature-first modules, TanStack Query + local state, shadcn/ui design system, Nginx Docker build, typed API layer.

### Lessons learned
- Vite 6 uses `tsconfig.app.json` + `tsconfig.node.json` split by default, not a single `tsconfig.json`. Path aliases must be configured in the right tsconfig.
- TypeScript 5.8+ deprecates `baseUrl` in favor of paths-only resolution with `moduleResolution: "bundler"`. Vite's resolve alias is still needed for the dev server.
- shadcn/ui Sheet component uses `@radix-ui/react-dialog`, not `@radix-ui/react-sheet` — the latter doesn't exist.
- jsdom doesn't provide `localStorage` or `matchMedia` — must be mocked in the test setup file.
- The `renderWithProviders` pattern (custom render wrapping all providers) is essential for testing components that use routing, queries, or theme.

### Next steps
- ✅ Phase 2 complete — Backend, Database, Docker, AI Infrastructure, Frontend Foundation
- **Phase 3 — Requirement Analysis Module** (first end-to-end business feature)
  - Backend: `app/modules/requirement_analysis/` with router, service, models, prompts, repository
  - Frontend: `src/modules/requirement-analysis/` with pages, components, hooks
  - AI integration: use the OpenRouter provider via the AI infrastructure layer
- Future phases: API Test Generation, Failure Analysis, additional providers

---

## 2026-07-02 — Phase 3: Requirement Analysis Module

### What we did
- **Built the complete Requirement Analysis module** — first end-to-end business feature of QPilot. Full vertical slice from API to frontend UI.

### Backend (`app/modules/requirement_analysis/`)

- **Pydantic schemas** (`models.py`) — 10+ strongly typed sections: `FunctionalTestCase`, `NegativeTestCase`, `BoundaryTestCase`, `EdgeCase`, `Risk`, `Assumption`, `MissingRequirement`, `SuggestedQuestion`, `AutomationCandidate`, `PriorityAssessment`. Each model has proper validation, enums for priority/severity/feasibility, and sensible defaults.
- **Input schema** (`AnalysisRequest`) — accepts plain text, Markdown, or acceptance criteria with optional title and context. Validated with min/max length constraints.
- **Repository** (`repository.py`) — `RequirementAnalysisRepository` extends `BaseRepository[AnalysisSession]` with `list_sessions()` (filtered by `REQUIREMENT_ANALYSIS` type, newest-first) and `get_with_output()` methods.
- **Service** (`service.py`) — `RequirementAnalysisService` orchestrates the end-to-end pipeline: create session → render prompt → call AI provider → parse response → update session with results → return structured `AnalysisResponse`. Includes proper error handling: marks session as `FAILED` on errors, re-raises known exception types (`ProviderUnavailableError`, `InvalidResponseError`, `AnalysisError`).
- **Router** (`router.py`) — three REST endpoints:
  - `POST /api/v1/requirements/analyze` — submit requirements for analysis
  - `GET /api/v1/requirements/sessions/{session_id}` — retrieve past analysis
  - `GET /api/v1/requirements/sessions` — list sessions with pagination
- **Exporters** (`exporters/`) — abstract base class + concrete `MarkdownExporter` and `JsonExporter` implementations. Factory function `get_exporter()` for format-by-name resolution.
- **Prompt templates** (`prompts/analysis/requirement-analysis/v1/`) — `system.md` and `examples.md` with complete JSON schema instructions, quality guidelines, and a full registration example with expected output.
- **ORM model updated** (`analysis_session.py`) — added 12 new columns: `input_source_type`, `input_content`, `input_filename`, `output_data`, `output_format`, `provider_used`, `model_used`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`, `error_message`. All nullable for backward compatibility.
- **Alembic migration** (`a1b2c3d4e5f6_add_analysis_fields.py`) — additive migration with `ADD COLUMN IF NOT EXISTS` for idempotency. No existing data migration needed.
- **app lifespan updated** (`main.py`) — `PromptManager` initialized during startup and stored on `app.state.prompt_manager`. Requirement analysis router registered in v1 API aggregator.

### Frontend (`frontend/src/modules/requirement-analysis/`)

- **TypeScript types** (`types/index.ts`) — mirrors all backend Pydantic models with proper TypeScript interfaces, enums (union types), and nested structures.
- **API services** (`services/requirement-analysis.ts`) — typed service functions for all three endpoints: `analyzeRequirements()`, `getAnalysisSession()`, `listAnalysisSessions()`.
- **TanStack Query hooks** (`hooks/use-requirement-analysis.ts`) — `useAnalyzeRequirements()` (mutation with cache invalidation), `useAnalysisSession()` (query with session ID), `useAnalysisSessions()` (paginated list query).
- **Components:**
  - `RequirementEditor` — text area with source type selector (plain text / Markdown / acceptance criteria), character count, error display, submit button
  - `SectionCard` — reusable card wrapper with title, icon, count badge, empty state message, color variant (success/danger/warning/info)
  - `SectionContent` — specialized renderers for each section: test case cards (with priority badge, preconditions, steps, expected result, tags), edge cases, risks (with severity badge, likelihood, mitigation), assumptions, missing requirements, suggested questions, automation candidates table, priority assessment block
  - `AnalysisResults` — complete results display with summary bar (provider/model/token/latency metadata), all 10+ section cards in structured grid, export/download buttons
  - `ExportActions` — dropdown with copy-as-JSON, copy-as-Markdown, download JSON, download Markdown
- **Pages:**
  - `RequirementAnalysisPage` — main workflow page: editor → submission → results display → new analysis
  - `SessionDetailPage` — past session viewer with loading/error/not-found states
- **Module index** (`index.ts`) — clean public API exporting all types, components, hooks, services, and pages.
- **App integration:**
  - Routes registered in `router.tsx`: `/requirements/analyze` and `/requirements/sessions/:sessionId`
  - Sidebar updated with "Requirement Analysis" nav item
  - Dashboard home page updated — Requirement Analysis card is now a live link (not "Coming soon")

### Testing

- **Backend: 48 new tests** across 4 files:
  - `test_models.py` (18 tests) — validates all Pydantic schemas, validation rules, roundtrip serialization
  - `test_exporters.py` (12 tests) — Markdown exporter structure/content, JSON exporter validity/roundtrip/pretty-printing, factory function
  - `test_service.py` (9 tests) — analysis success path, error handling (provider unavailable, invalid response, missing provider), session retrieval (existing, missing, no output), session listing
  - `test_router.py` (9 tests) — endpoint validation (success, empty content, missing content, source types, invalid source), 404 handling, list pagination
- **Frontend: 17 new tests** across 3 files:
  - `types.test.ts` (6 tests) — TypeScript type shape validation, JSON roundtrip
  - `components.test.tsx` (8 tests) — SectionCard rendering, FunctionalTestCases, RisksList, AssumptionsList, PriorityAssessmentBlock
  - `services.test.ts` (3 tests) — API service functions with mocked Axios client
- **Total: 131 backend + 34 frontend = 165 passing tests**

### Key decisions made
1. **Single `AnalysisSession` model with type discriminator** — Requirement-specific fields (input_content, output_data) are nullable columns on the existing `analysis_sessions` table, not a separate table. This keeps queries simple and avoids JOINs for history/listing.
2. **Alerts are synchronous with the request** — No polling, no websockets. The `POST /analyze` endpoint waits for the AI provider and returns the complete result. Simpler MVP at the cost of longer request duration.
3. **Exporters are server-side** — Both Markdown and JSON exporters live on the backend. The frontend has client-side copy/download as a convenience but can always fetch the server-generated format.
4. **Prompt examples are essential for quality** — The `examples.md` file provides a complete sample analysis with expected JSON output. This significantly improves initial AI response quality compared to schema-only prompts.
5. **Frontend module structure mirrors backend** — `src/modules/requirement-analysis/` has the same internal structure as `app/modules/requirement_analysis/`: types, services, hooks, components, pages. This makes it easy to understand which backend code corresponds to which frontend code.

### Architecture validation
- **ADR-001** ✅ — Service uses `ProviderRegistry.get()` and `AIProvider.generate()` through the AI infrastructure layer. No provider-specific code in the module.
- **ADR-002** ✅ — Prompt templates live in `prompts/analysis/requirement-analysis/v1/`. Service uses `PromptManager.load()` to render them.
- **ADR-003** ✅ — Module follows the standard structure exactly: `router.py`, `service.py`, `models.py`, `repository.py`, `tests/`. No cross-module imports.
- **ADR-004** ✅ — Schema extended with nullable columns. Existing data not affected.
- **ADR-005** ✅ — Endpoints follow the response envelope pattern: `{ data, meta }`. Paginated endpoints use `PaginationMeta`. Error responses use `{ error, meta }`.
- **ADR-006** ✅ — Frontend module follows feature-first pattern. Uses TanStack Query for server state, Axios typed services, shared UI components.

### Lessons learned
- **Mocking the PromptManager** in service tests revealed that the `load()` method expects real template files. Module-specific test fixtures need to mock both `AIProvider` and `PromptManager` to avoid filesystem dependencies.
- **Router integration tests** need the database schema to exist. Using `LifespanManager` to simulate app lifespan must be followed by `await db_manager.create_all()` to create tables in the in-memory SQLite database.
- **JSON response validation in tests** — the AI provider's response must match the `RequirementAnalysisResult` schema exactly. Mocking the provider response inline is simpler than using the test fixtures for fine-grained control.
- **The 10+ section model** produces a large but well-structured response. The `model_dump(mode="json")` pattern handles datetime serialization automatically, which saved time during frontend integration.
- **Frontend component testing** for analysis results doesn't require API mocking — we can pass sample data directly as props. The heavy rendering (nested cards, tables) validates the component tree renders without errors.

### Next steps
- Phase 4 — API Test Generation module (second business feature)
- Phase 5 — Failure Analysis module
- Additional AI providers (OpenAI, Claude, Gemini, Groq)
- History/listing UI improvements (search, filter, sort)

---

## Journal Usage Guide

- **Entry format:** `YYYY-MM-DD — Title`
- **Content:** What we did, why we chose this approach, alternatives considered, trade-offs, what we learned
- **Tone:** Professional but honest. Include mistakes and course corrections — these are as valuable as successes.
- **Frequency:** At minimum, one entry per Phase. More entries for significant discoveries or course changes.
