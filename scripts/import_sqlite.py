"""One-time copy of the old SQLite database into Postgres.

Runs on every container start (see docker-entrypoint.sh) but only does anything when the
old SQLite file is still present and the Postgres database has no users yet. After a
successful import the SQLite file is renamed, so it never runs twice; the renamed file is
kept as a backup.

Usage: python -m scripts.import_sqlite [path-to-sqlite-file]
"""
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, insert, select
from sqlalchemy.engine import make_url

import app.models  # noqa: F401 registers all models on Base.metadata
from app.core.config import settings
from app.db.base import Base
from app.models.user import User

DEFAULT_SOURCE = Path("/app/data/db.sqlite3")
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _sync_url(url: str) -> str:
    parsed = make_url(url)
    backend = parsed.get_backend_name()
    driver = {"postgresql": "postgresql+psycopg"}.get(backend, backend)
    return parsed.set(drivername=driver).render_as_string(hide_password=False)


def _upgrade(async_url: str) -> None:
    cfg = Config(str(ALEMBIC_INI))
    cfg.attributes["database_url"] = async_url
    command.upgrade(cfg, "head")


def import_sqlite(source: Path) -> None:
    if make_url(settings.DATABASE_URL).get_backend_name() != "postgresql":
        print("import_sqlite: DATABASE_URL is not Postgres; nothing to do")
        return
    if not source.exists():
        print(f"import_sqlite: no SQLite file at {source}; nothing to do")
        return

    target = create_engine(_sync_url(settings.DATABASE_URL))
    with target.connect() as conn:
        if conn.execute(select(func.count()).select_from(User)).scalar_one() > 0:
            print("import_sqlite: Postgres already has users; skipping import (SQLite file left untouched)")
            return

    # Bring a copy of the old database up to the current schema, so its columns line up.
    with tempfile.TemporaryDirectory() as tmp:
        work_copy = Path(tmp) / "source.db"
        shutil.copy2(source, work_copy)
        _upgrade(f"sqlite+aiosqlite:///{work_copy.as_posix()}")

        src = create_engine(f"sqlite:///{work_copy.as_posix()}")
        counts = {}
        with src.connect() as src_conn, target.begin() as dst_conn:
            for table in Base.metadata.sorted_tables:
                rows = [dict(r) for r in src_conn.execute(select(table)).mappings()]
                if rows:
                    dst_conn.execute(insert(table), rows)
                counts[table.name] = len(rows)
        src.dispose()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    source.rename(source.with_name(f"{source.name}.imported-{stamp}"))
    print("import_sqlite: imported " + ", ".join(f"{n} {t}" for t, n in counts.items()))


if __name__ == "__main__":
    import_sqlite(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE)
