# Deployment

The API runs in Docker (uvicorn, no pm2) via `docker-compose.yml`. Production and
staging share one VPS as two compose projects:

| Environment | Branch    | Folder on VPS                    | Compose project       | Port |
|-------------|-----------|----------------------------------|-----------------------|------|
| Production  | `main`    | `/home/deploy/Duel_Domain`         | `duel-domain`         | 8000 |
| Staging     | `staging` | `/home/deploy/Duel_Domain-staging` | `duel-domain-staging` | 8001 |

Migrations (`alembic upgrade head`) run automatically each time the container starts.
The SQLite database lives in each project's `data` Docker volume, so it survives rebuilds.

## Automatic deploys

Pushing to `main` or `staging` runs `.github/workflows/deploy-*.yml`. It builds the image
in CI, then SSHes into the VPS, runs `git pull` and `docker compose up -d --build`.

Required repo secrets: `VPS_HOST`, `VPS_USER` (`deploy`), `VPS_SSH_KEY`.

## First-time VPS setup (Ubuntu)

```sh
scp scripts/server_setup.sh root@<vps-ip>:/root/
ssh root@<vps-ip> sh /root/server_setup.sh
```

The first run installs Docker, creates the `deploy` user and prints two keys: a deploy key
to add on GitHub and the private key for the `VPS_SSH_KEY` secret. Add both, then run the
script again. The second run clones both branches, writes a `.env` with a random
`SECRET_KEY` for each, and starts the containers.

## Configuration

Each environment's `.env` (see `.env.example`) must set `SECRET_KEY` (32+ characters);
the app refuses to start without it. Password reset emails need the `SMTP_*` settings;
until `SMTP_HOST` is set, reset codes are not sent. After editing `.env`, apply it with
`docker compose -p <project> up -d`.

## Day-to-day commands (on the VPS, as `deploy`)

```sh
cd ~/Duel_Domain
docker compose -p duel-domain ps              # status
docker compose -p duel-domain logs -f api     # logs
docker compose -p duel-domain restart api     # restart
docker compose -p duel-domain exec api python -m scripts.make_admin you@example.com
```

Use `-p duel-domain-staging` inside `~/Duel_Domain-staging` for staging.

## Moving to a new server

Back up the database from the old server, then restore it on the new one before starting:

```sh
# old server
docker compose -p duel-domain cp api:/app/data/db.sqlite3 ./db-backup.sqlite3
# new server (after setup)
docker compose -p duel-domain cp ./db-backup.sqlite3 api:/app/data/db.sqlite3
docker compose -p duel-domain exec -u root api chown app:app /app/data/db.sqlite3
docker compose -p duel-domain restart api
```

## Running locally

```sh
cp .env.example .env   # then set SECRET_KEY
docker compose up --build
```

Tests:

```sh
pip install -r requirements-dev.txt
pytest
```

API: http://localhost:8000/swagger/
