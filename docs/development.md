# Development Guide

## Quick Start

Prerequisites:

- [Docker Desktop](https://docs.docker.com/desktop/) (includes Docker Compose)
- Python 3.11+ (for local `uv sync` and IDE support)
- [uv](https://docs.astral.sh/uv/) (fast Python package manager, optional but recommended)
- Node.js 20+ (for frontend development)
- npm 10+ (comes with Node.js)

### Full Stack (Docker)

```bash
# 1. Set up local Python environment (for tests, linting, IDE)
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env if needed (defaults work for Docker Compose)

# 3. Start the entire stack
docker compose up --build
```

The stack is available at:

| Service     | URL                              |
|-------------|----------------------------------|
| Frontend    | **http://localhost:3000**        |
| Backend     | **http://localhost:8000**        |
| API Docs    | **http://localhost:8000/docs**   |
| PostgreSQL  | **localhost:5432**               |

Stop with `Ctrl+C` or `docker compose down`.

### Frontend Development (with HMR)

For frontend development with hot module replacement:

```bash
# Terminal 1: Start backend + database
docker compose up postgres backend -d

# Terminal 2: Start Vite dev server
cd frontend
npm install
npm run dev
```

The Vite dev server runs at **http://localhost:3000** with HMR enabled.
The backend's CORS configuration already allows this origin.

---

## Project Structure

```
├── app/                    # Backend application source
│   ├── ai/                 # AI infrastructure layer
│   ├── api/                # API routing & middleware
│   └── infrastructure/     # Shared infrastructure (config, db, logging)
├── frontend/               # Frontend SPA (React + Vite + shadcn/ui)
│   ├── src/
│   │   ├── app/            # Application setup (providers, router, pages)
│   │   ├── components/     # Shared UI components (shadcn/ui + custom)
│   │   ├── layouts/        # App layouts (sidebar, topbar, root)
│   │   ├── modules/        # Feature modules (one per feature)
│   │   ├── services/       # Typed API client layer (Axios)
│   │   ├── hooks/          # Shared React hooks
│   │   ├── lib/            # Utilities (cn, constants)
│   │   └── types/          # Shared TypeScript types
│   ├── tests/              # Frontend test suite
│   ├── Dockerfile          # Multi-stage Nginx build
│   └── nginx.conf          # Nginx config with SPA fallback + API proxy
├── prompts/                # Prompt templates (versioned Markdown)
├── alembic/                # Database migrations
├── tests/                  # Backend test suite (Python)
├── docs/                   # Architecture & development docs
├── Dockerfile              # Backend multi-stage Docker image
├── docker-compose.yml      # Base Compose configuration (3 services)
├── docker-compose.override.yml  # Dev overrides (auto-loaded)
├── .env.example            # Documented environment variables
├── pyproject.toml          # Backend project metadata & dependencies
└── uv.lock                 # Locked Python dependency versions
```

---

## Backend Development

### Running Backend Tests

```bash
# All tests (with coverage)
uv run pytest

# Specific test files
uv run pytest tests/test_health.py

# Watch mode (install pytest-watch separately)
# uv run ptw
```

Tests use SQLite in-memory, so they require only Python — no Docker or PostgreSQL needed.

## Frontend Development

### Architecture

The frontend follows a **feature-first** architecture (see [ADR-006](./adr/ADR-006-frontend-architecture.md)):

- **`src/app/`** — Application infrastructure (providers, router, app-level pages)
- **`src/layouts/`** — Persistent shell (sidebar, topbar, root layout)
- **`src/components/`** — Shared UI components (shadcn/ui primitives, error boundary, loading/empty states)
- **`src/modules/`** — Feature modules (one directory per feature, currently empty for Phase 3+)
- **`src/services/`** — Typed API client layer (Axios + interceptors + service functions)
- **`src/hooks/`** — Shared custom hooks (useHealth, useTheme)
- **`src/lib/`** — Pure utility functions (cn(), constants)

### Running Frontend Tests

```bash
cd frontend

# Run all tests
npx vitest run

# Watch mode
npx vitest

# With UI
npx vitest --ui
```

### Building for Production

```bash
cd frontend
npm run build     # Outputs to frontend/dist/
```

The Docker production build uses Nginx (see `frontend/Dockerfile` and `frontend/nginx.conf`).

### Frontend Conventions

| Convention | Rule |
|---|---|
| **Imports** | Use `@/` path alias: `import { Button } from "@/components/ui/button"` |
| **Components** | PascalCase filenames, named exports |
| **CSS** | Tailwind utility classes + shadcn/ui CSS variables |
| **API calls** | Always through `src/services/` — never raw Axios |
| **Server state** | TanStack Query hooks in `src/hooks/` |
| **Module boundaries** | A module never imports from another module's directory |

### Database Migrations

Migrations run **automatically** when the backend container starts (via `docker-entrypoint.sh`).

To create a new migration:

```bash
# Generate a migration from model changes (requires running PostgreSQL)
# Start PostgreSQL first: docker compose up postgres -d
docker compose run --rm backend alembic revision --autogenerate -m "description"

# Or create an empty migration for manual editing
docker compose run --rm backend alembic revision -m "description"
```

To roll back:

```bash
docker compose run --rm backend alembic downgrade -1
```

### Local Development without Docker

```bash
uv sync

# Start PostgreSQL (via Docker, optional)
docker compose up postgres -d

# Run the app
uv run uvicorn app.main:app --reload
```

### Logging

```bash
# Follow all logs
docker compose logs -f

# Backend only
docker compose logs -f backend

# Database only
docker compose logs -f postgres
```

---

## Docker Decisions

### Why `python:3.12-slim`?

The slim image is ~120 MB vs ~340 MB for the full `python:3.12` image. It includes only the minimal system libraries needed to run Python and pure-Python packages. Native packages like `asyncpg` ship their own pre-compiled wheels, so no build tools are needed at runtime.

### Why multi-stage?

The builder stage installs `gcc` (80 MB of build tools) for any native extensions that must compile from source. The runtime stage copies only the installed packages — no build tools leak into the final image. This reduces the attack surface and image size.

### Why run migrations in the entrypoint?

Every container start runs `alembic upgrade head`. This eliminates the "forgot to migrate" class of errors and is safe because Alembic applies only pending revisions. In production orchestrators (Kubernetes, ECS), this removes the need for an init container or separate job.

### Why a shell entrypoint instead of Python?

A shell script can `exec` the main process, replacing the shell PID with uvicorn's PID. This ensures Docker signals (SIGTERM) reach uvicorn directly — no double-fork, no zombie processes.

### Why `docker compose up --build` instead of plain `docker compose up`?

The `--build` flag forces a rebuild every time, which is useful during development as dependencies change. For day-to-day work where only Python source changes, you can omit `--build` — only the app layer is invalidated.

### Why a separate override file?

Docker Compose automatically loads `docker-compose.override.yml` and merges it with `docker-compose.yml`. This keeps the base configuration production-safe while enabling development features (code mounting, `--reload`, `.env` files) without environment-specific commands.

---

## Troubleshooting

### Backend won't start: "Cannot connect to database"

```bash
# Check if PostgreSQL is healthy
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# If PostgreSQL failed to start, reset the data volume
docker compose down -v
docker compose up --build
```

### Port conflict (port 5432 or 8000 already in use)

Edit `docker-compose.yml` to change the host port:

```yaml
services:
  postgres:
    ports:
      - "5433:5432"   # Change 5433 to any available port
  backend:
    ports:
      - "8001:8000"   # Change 8001 to any available port
```

### Alembic migration fails

```bash
# Check the error
docker compose logs backend

# Reset database and re-run
docker compose down -v
docker compose up --build
```

### Tests pass locally but fail in CI

Ensure CI uses the same Python version (3.11+) and installs with `uv sync` (or `pip install -e ".[dev]"`). Tests use SQLite, so no database service is needed.

### Permission denied on mounted files

On Linux, files created inside the container may be owned by `uid:1001` (the `cypherpilot` user). Run `sudo chown -R $(id -u):$(id -g) .` in the project root to reset ownership.

This does not affect macOS or Windows.

---

## Production Deployment Considerations

The current setup is designed for single-container development. For production, consider:

### Image Registry

```bash
# Build and push to a registry
docker build -t ghcr.io/your-org/cypherpilot:latest .
docker push ghcr.io/your-org/cypherpilot:latest
```

### Production Compose File

Use `docker-compose.prod.yml` with these overrides:

```yaml
services:
  backend:
    # No volume mounts
    # No --reload
    # Environment from orchestration platform, not .env file
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: "512M"
```

### Environment Variables in Production

- **Secrets**: Use Docker secrets, Kubernetes Secrets, or your orchestration platform's secret store — never `.env` files.
- **Database**: Use a managed PostgreSQL service (RDS, Cloud SQL) or a dedicated PostgreSQL container with persistent storage.
- **Logging**: Set `LOG_LEVEL=WARNING` in production. Collect logs via `docker logs` → stdout/stderr → your log aggregator.

### Scaling

- The backend is stateless (sessions are in the database). Scale horizontally with `docker compose up --scale backend=3`.
- Add a reverse proxy (Traefik, nginx) in front of the backend for TLS termination and load balancing.
- PostgreSQL should be deployed as a managed service or with replication for production scale.

### Migrations in Production

The entrypoint script runs migrations on every startup. For production deployments:

- **Zero-downtime**: Run `alembic upgrade head` before the new deployment (as a separate step or init container).
- **Rollback**: If a migration fails, the old version should still be running. Use blue-green deployment to prevent downtime.
