#!/bin/sh
set -e

# Apply any pending migrations before the API starts serving.
alembic upgrade head

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WEB_CONCURRENCY:-1}"
