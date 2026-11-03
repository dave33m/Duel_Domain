import os
import tempfile
from pathlib import Path

# Configure the app before anything imports it: the engine and settings are module-level.
# Tests use a throwaway SQLite file unless TEST_DATABASE_URL points at a (disposable!) Postgres.
_DB_PATH = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{_DB_PATH.as_posix()}"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"
os.environ["DEBUG"] = "False"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import update  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.limiter import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.email_service import EmailService  # noqa: E402

limiter.enabled = False

PASSWORD = "Sturdy-Passw0rd!"


@pytest.fixture(autouse=True)
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


class Outbox(list):
    """Emails the app tried to send during a test."""

    def to(self, address: str, template: str | None = None) -> list[dict]:
        return [m for m in self if address in m["recipients"] and template in (None, m["template"])]

    def code_for(self, address: str, template: str) -> str:
        return self.to(address, template)[-1]["context"]["code"]


@pytest.fixture(autouse=True)
def outbox(monkeypatch) -> Outbox:
    box = Outbox()

    def fake_queue(recipients, subject, template, context):
        box.append({"recipients": recipients, "subject": subject, "template": template, "context": context})

    monkeypatch.setattr(EmailService, "queue", staticmethod(fake_queue))
    return box


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class Account:
    def __init__(self, client: AsyncClient, email: str, username: str, token: str, player_id: str):
        self.client = client
        self.email = email
        self.username = username
        self.token = token
        self.player_id = player_id

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    async def get(self, url, **kw):
        return await self.client.get(url, headers=self.headers, **kw)

    async def post(self, url, **kw):
        return await self.client.post(url, headers=self.headers, **kw)

    async def put(self, url, **kw):
        return await self.client.put(url, headers=self.headers, **kw)

    async def delete(self, url, **kw):
        return await self.client.delete(url, headers=self.headers, **kw)


@pytest.fixture
def make_account(client):
    async def _make(username: str, admin: bool = False) -> Account:
        email = f"{username}@example.com"
        r = await client.post("/auth/signup/", json={"email": email, "username": username, "password": PASSWORD})
        assert r.status_code == 201, r.text
        if admin:
            async with AsyncSessionLocal() as db:
                await db.execute(update(User).where(User.email == email).values(is_admin=True))
                await db.commit()
        r = await client.post("/auth/signin/", json={"email": email, "password": PASSWORD})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        me = await client.get("/player/me/", headers={"Authorization": f"Bearer {token}"})
        return Account(client, email, username, token, me.json()["id"])

    return _make


@pytest.fixture
async def admin(make_account):
    return await make_account("admin_user", admin=True)


@pytest.fixture
async def game(admin):
    r = await admin.post("/game/create/", json={"name": "FIFA 26", "platform": "playstation"})
    assert r.status_code == 201, r.text
    return r.json()["game_id"]
