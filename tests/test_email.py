import pytest

from app.core.config import settings
from app.services.email_service import EmailService, build_mail_client
from tests.conftest import PASSWORD

VERIFY = "verify_email.html"


async def _signup(client, username="alice"):
    email = f"{username}@example.com"
    r = await client.post("/auth/signup/", json={"email": email, "username": username, "password": PASSWORD})
    assert r.status_code == 201, r.text
    return email


async def _token(client, email, password=PASSWORD):
    r = await client.post("/auth/signin/", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


async def test_signup_sends_verification_and_alerts_admins(client, outbox, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_NOTIFY_EMAILS", "ops@duel-domain.com, owner@duel-domain.com")
    email = await _signup(client)

    assert len(outbox.to(email, VERIFY)) == 1
    alert = outbox.to("ops@duel-domain.com", "admin_new_signup.html")
    assert alert and alert[0]["recipients"] == ["ops@duel-domain.com", "owner@duel-domain.com"]
    assert alert[0]["context"]["username"] == "alice"
    assert not outbox.to(email, "welcome.html")  # welcome waits for verification

    assert (await _token(client, email))["email_verified"] is False


async def test_no_admin_alert_when_unconfigured(client, outbox):
    await _signup(client)
    assert not [m for m in outbox if m["template"] == "admin_new_signup.html"]


async def test_verify_email_then_welcome(client, outbox):
    email = await _signup(client)

    r = await client.post("/auth/verify-email/", json={"email": email, "code": "000000" if outbox.code_for(email, VERIFY) != "000000" else "111111"})
    assert r.status_code == 400

    r = await client.post("/auth/verify-email/", json={"email": email, "code": outbox.code_for(email, VERIFY)})
    assert r.status_code == 200 and r.json()["message"] == "Email verified"
    assert len(outbox.to(email, "welcome.html")) == 1

    signin = await _token(client, email)
    assert signin["email_verified"] is True
    me = await client.get("/player/me/", headers={"Authorization": f"Bearer {signin['token']}"})
    assert me.json()["email_verified"] is True

    r = await client.post("/auth/verify-email/", json={"email": email, "code": "123456"})
    assert r.json()["message"] == "Email already verified"
    assert len(outbox.to(email, "welcome.html")) == 1


async def test_resend_verification_replaces_code_and_reveals_nothing(client, outbox):
    email = await _signup(client)
    first = outbox.code_for(email, VERIFY)

    unknown = await client.post("/auth/resend-verification/", json={"email": "nobody@example.com"})
    known = await client.post("/auth/resend-verification/", json={"email": email})
    assert unknown.json() == known.json()
    assert len(outbox.to(email, VERIFY)) == 2

    second = outbox.code_for(email, VERIFY)
    if first != second:
        r = await client.post("/auth/verify-email/", json={"email": email, "code": first})
        assert r.status_code == 400  # superseded
    r = await client.post("/auth/verify-email/", json={"email": email, "code": second})
    assert r.status_code == 200

    await client.post("/auth/resend-verification/", json={"email": email})
    assert len(outbox.to(email, VERIFY)) == 2  # already verified: nothing sent


async def test_change_password_two_steps(client, outbox):
    email = await _signup(client)
    old = await _token(client, email)
    headers = {"Authorization": f"Bearer {old['token']}"}

    r = await client.post("/auth/change-password/request/", json={"current_password": "Wrong-Passw0rd!"}, headers=headers)
    assert r.status_code == 400
    assert not outbox.to(email, "password_change_code.html")

    r = await client.post("/auth/change-password/request/", json={"current_password": PASSWORD}, headers=headers)
    assert r.status_code == 200
    code = outbox.code_for(email, "password_change_code.html")

    # A rejected new password doesn't use up the code.
    r = await client.post("/auth/change-password/confirm/", json={"code": code, "new_password": PASSWORD}, headers=headers)
    assert r.status_code == 400

    new_password = "Fresh-Passw0rd-42"
    r = await client.post("/auth/change-password/confirm/", json={"code": code, "new_password": new_password}, headers=headers)
    assert r.status_code == 200, r.text
    new_token = r.json()["token"]

    assert (await client.get("/player/me/", headers=headers)).status_code == 401
    assert (await client.get("/player/me/", headers={"Authorization": f"Bearer {new_token}"})).status_code == 200
    assert len(outbox.to(email, "password_changed.html")) == 1
    await _token(client, email, new_password)


async def test_change_password_requires_login(client):
    r = await client.post("/auth/change-password/request/", json={"current_password": PASSWORD})
    assert r.status_code == 401


async def test_password_reset_sends_changed_notice(client, outbox):
    email = await _signup(client)
    await client.post("/auth/forgot-password/", json={"email": email})
    code = outbox.code_for(email, "password_reset.html")
    r = await client.post("/auth/reset-password/", json={"email": email, "otp": code, "new_password": "Fresh-Passw0rd-42"})
    assert r.status_code == 200
    assert len(outbox.to(email, "password_changed.html")) == 1


@pytest.mark.parametrize(
    "template, context, expected",
    [
        ("verify_email.html", {"username": "alice", "code": "482913", "minutes": 60}, "482913"),
        ("welcome.html", {"username": "alice"}, "Welcome to Duel Domain"),
        ("password_reset.html", {"username": "alice", "code": "482913", "minutes": 10}, "482913"),
        ("password_change_code.html", {"username": "alice", "code": "482913", "minutes": 10}, "482913"),
        ("password_changed.html", {"username": "alice"}, "password was just changed"),
        ("admin_new_signup.html", {"username": "alice", "email": "a@example.com", "user_id": "u-1"}, "a@example.com"),
    ],
)
async def test_templates_render_through_fastapi_mail(template, context, expected):
    client = build_mail_client(suppress_send=True)
    with client.record_messages() as sent:
        await EmailService.send(["alice@example.com"], "Subject", template, context, client=client)

    assert len(sent) == 1
    message = sent[0]
    assert "alice@example.com" in message["To"]
    assert settings.MAIL_FROM in message["From"]
    html = next(p for p in message.walk() if p.get_content_type() == "text/html").get_payload(decode=True).decode()
    assert expected in html
    assert "alice" in html or "a@example.com" in html


async def test_send_without_api_key_is_a_no_op(monkeypatch):
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    await EmailService.send(["alice@example.com"], "Subject", "welcome.html", {"username": "alice"})
