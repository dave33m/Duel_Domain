# Deployment

The API runs in Docker (uvicorn, no pm2) via `docker-compose.yml`. Production and
staging share one VPS as two compose projects:

| Environment | URL                                   | Branch    | Folder on VPS                      | Compose project       | Local port |
|-------------|---------------------------------------|-----------|------------------------------------|-----------------------|------------|
| Production  | https://api.duel-domain.com         | `main`    | `/home/deploy/Duel_Domain`         | `duel-domain`         | 8000       |
| Staging     | https://staging-api.duel-domain.com | `staging` | `/home/deploy/Duel_Domain-staging` | `duel-domain-staging` | 8001       |

The API containers listen on `127.0.0.1` only. Caddy (`/opt/caddy`, set up by
`scripts/setup_caddy.sh`) serves both over HTTPS and renews certificates automatically.

Each environment has its own Postgres 17 container (`db`) with data in its `pgdata` volume,
so it survives rebuilds. Postgres publishes no port; only the API container can reach it.
Migrations (`alembic upgrade head`) run automatically each time the API container starts.

The API previously used SQLite. On first start with Postgres, the old database in the
`data` volume is imported automatically (`scripts/import_sqlite.py`) and then renamed to
`db.sqlite3.imported-<timestamp>`, which is kept as a backup.

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

## HTTPS and domains

DNS for `duel-domain.com` is managed in Vercel (Domains -> duel-domain.com -> DNS Records).
The API needs two A records pointing at the VPS:

| Type | Name          | Value            |
|------|---------------|------------------|
| A    | `api`         | `104.207.70.132` |
| A    | `staging-api` | `104.207.70.132` |

Then, once the records resolve, run as root on the VPS:

```sh
sh /root/setup_caddy.sh
```

## Configuration

Each environment's `.env` (see `.env.example`) must set `SECRET_KEY` (32+ characters) and
`POSTGRES_PASSWORD`; neither container starts without them. Password reset emails need the `SMTP_*` settings;
until `SMTP_HOST` is set, reset codes are not sent. `CORS_ORIGINS` lists the frontend
origins allowed to call the API (e.g. `https://duel-domain.com,https://www.duel-domain.com`);
it defaults to `*`. After editing `.env`, apply it with
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

## Backups

`scripts/backup_db.sh` dumps an environment's database to `~/backups/<project>/` and deletes
dumps older than 14 days. `server_setup.sh` schedules it nightly via the `deploy` user's
crontab (`crontab -l` to see it); output goes to `~/backups/backup.log`. Run one by hand:

```sh
sh ~/Duel_Domain/scripts/backup_db.sh duel-domain ~/Duel_Domain
```

Restore a dump (replaces the current data):

```sh
cd ~/Duel_Domain
docker compose -p duel-domain exec -T db pg_restore -U duel -d duel_domain --clean --if-exists < ~/backups/duel-domain/<file>.dump
```

The dumps live on the same VPS, so also copy them somewhere else now and then, e.g. from
your PC: `scp -r deploy@104.207.70.132:backups ./duel-domain-backups`.

## Moving to a new server

Take a fresh backup on the old server, run the setup on the new one, copy the dump across,
and restore it with the command above.

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
