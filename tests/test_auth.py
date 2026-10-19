import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services import otp_service
from tests.conftest import PASSWORD


@pytest.fixture
def sent_codes(monkeypatch):
    """Captures reset codes instead of emailing them."""
    sent = []

    async def fake_send(to, subject, body):
        sent.append((to, body))

    monkeypatch.setattr(otp_service.EmailService, "send", fake_send)
    return sent


def _code_from(body: str) -> str:
    return next(word.rstrip(".") for word in body.split() if word.rstrip(".").isdigit() and len(word.rstrip(".")) == 6)


async def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


async def test_short_secret_key_is_rejected(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "too-short")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


async def test_signup_normalizes_email_and_blocks_case_duplicates(client):
    r = await client.post("/auth/signup/", json={"email": "Mixed@Example.com", "username": "mixer", "password": PASSWORD})
    assert r.status_code == 201

    r = await client.post("/auth/signup/", json={"email": "mixed@example.COM", "username": "other", "password": PASSWORD})
    assert r.status_code == 400
    assert r.json()["detail"] == "Email already exists"

    r = await client.post("/auth/signin/", json={"email": "MIXED@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["email"] == "mixed@example.com"


async def test_username_is_validated_and_unique_ignoring_case(client, make_account):
    await make_account("taken_name")
    r = await client.post("/auth/signup/", json={"email": "x@example.com", "username": "TAKEN_NAME", "password": PASSWORD})
    assert r.status_code == 400

    r = await client.post("/auth/signup/", json={"email": "y@example.com", "username": "bad name!", "password": PASSWORD})
    assert r.status_code == 422


async def test_signin_with_wrong_password_fails(client, make_account):
    acct = await make_account("alice")
    r = await client.post("/auth/signin/", json={"email": acct.email, "password": "Wrong-Passw0rd!"})
    assert r.status_code == 401


async def test_send_otp_endpoint_is_gone(client):
    r = await client.post("/auth/send-otp/", json={})
    assert r.status_code == 404


async def test_forgot_password_does_not_reveal_accounts(client, make_account, sent_codes):
    acct = await make_account("alice")
    known = await client.post("/auth/forgot-password/", json={"email": acct.email})
    unknown = await client.post("/auth/forgot-password/", json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert "user_id" not in known.json()
    assert [to for to, _ in sent_codes] == [acct.email]


async def test_password_reset_flow_revokes_old_tokens(client, make_account, sent_codes):
    acct = await make_account("alice")
    assert (await acct.get("/player/me/")).status_code == 200

    await client.post("/auth/forgot-password/", json={"email": acct.email})
    code = _code_from(sent_codes[-1][1])

    new_password = "Brand-New-Passw0rd"
    r = await client.post("/auth/reset-password/", json={"email": acct.email, "otp": code, "new_password": new_password})
    assert r.status_code == 200, r.text

    assert (await acct.get("/player/me/")).status_code == 401  # token from before the reset

    r = await client.post("/auth/signin/", json={"email": acct.email, "password": new_password})
    assert r.status_code == 200
    r = await client.get("/player/me/", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert r.status_code == 200

    # The code is single-use.
    r = await client.post("/auth/reset-password/", json={"email": acct.email, "otp": code, "new_password": "Another-Passw0rd"})
    assert r.status_code == 400


async def test_reset_code_is_burned_after_too_many_wrong_guesses(client, make_account, sent_codes):
    acct = await make_account("alice")
    await client.post("/auth/forgot-password/", json={"email": acct.email})
    code = _code_from(sent_codes[-1][1])
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(otp_service.MAX_ATTEMPTS):
        r = await client.post("/auth/reset-password/", json={"email": acct.email, "otp": wrong, "new_password": "Brand-New-Passw0rd"})
        assert r.status_code == 400

    r = await client.post("/auth/reset-password/", json={"email": acct.email, "otp": code, "new_password": "Brand-New-Passw0rd"})
    assert r.status_code == 400


async def test_deactivated_user_is_locked_out(client, make_account, admin):
    acct = await make_account("alice")
    r = await admin.delete(f"/auth/user/{(await _user_id(admin, acct))}/")
    assert r.status_code == 200

    assert (await acct.get("/player/me/")).status_code == 401
    r = await client.post("/auth/signin/", json={"email": acct.email, "password": PASSWORD})
    assert r.status_code == 401

    # Hidden from public listings, but the record (and duel history) remains.
    board = (await client.get("/player/leaderboard/")).json()["leaderboard"]
    assert acct.username not in [e["username"] for e in board]
    users = (await admin.get("/auth/users/")).json()["users"]
    assert any(u["username"] == acct.username and u["is_active"] is False for u in users)


async def test_admin_cannot_deactivate_self(admin):
    r = await admin.delete(f"/auth/user/{(await _user_id(admin, admin))}/")
    assert r.status_code == 400


async def _user_id(admin, acct) -> str:
    users = (await admin.get("/auth/users/")).json()["users"]
    return next(u["id"] for u in users if u["username"] == acct.username)
