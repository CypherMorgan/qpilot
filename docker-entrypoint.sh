#!/bin/sh
# docker-entrypoint.sh — QPilot container entrypoint
#
# Runs database migrations on every startup, then hands off to the
# main process (uvicorn).  This ensures the database schema is always
# up-to-date regardless of how the container was started.
#
# Why run migrations at startup?
#   - Eliminates the "forgot to migrate" class of errors.
#   - Works trivially with both `docker compose up` and orchestrators.
#   - Idempotent: `alembic upgrade head` applies only pending revisions.
#
# Why a shell script instead of Python?
#   - Simpler process management (no Python runtime needed for this).
#   - `exec` replaces the shell process with uvicorn, passing signals
#     correctly (no double-fork / zombie process issues).

set -e

echo "==> Running database migrations..."
alembic upgrade head
echo "==> Migrations complete."

echo "==> Starting application..."
exec "$@"
