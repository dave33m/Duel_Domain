#!/bin/sh
set -e

# Apply any pending migrations before the API starts serving.
alembic upgrade head

# The port is only reachable through the local reverse proxy (see docker-compose.yml), so
# trust its X-Forwarded-For header; otherwise every user shares the proxy's IP and the
# rate limiter throttles them all together.
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WEB_CONCURRENCY:-1}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
