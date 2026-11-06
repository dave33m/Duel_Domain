PASSWORD = "Sturdy-Passw0rd!"

GAME_PAYLOAD = {
    "name": "FIFA 26",
    "platform": "playstation",
    "banner": "https://cdn.example.com/fifa-26.png",
    "game_type": "sports",
    "match_modes": [
        {"name": "1 v 1", "description": "Head to head"},
        {"name": "2 v 2", "description": "Two players per side"},
    ],
}


async def test_admin_signin_rejects_regular_users_and_allows_admins(client, make_account, admin):
    alice = await make_account("alice")

    r = await client.post(
        "/auth/admin/signin/", json={"email": alice.email, "password": PASSWORD}
    )
    assert r.status_code == 403

    r = await client.post(
        "/auth/admin/signin/", json={"email": admin.email, "password": "Wrong-Passw0rd!"}
    )
    assert r.status_code == 401

    r = await client.post(
        "/auth/admin/signin/", json={"email": admin.email, "password": PASSWORD}
    )
    assert r.status_code == 200
    assert r.json()["is_admin"] is True
    assert r.json()["token"]


async def test_admin_can_create_update_and_delete_games(client, admin, make_account):
    alice = await make_account("alice")

    r = await admin.post("/game/create/", json=GAME_PAYLOAD)
    assert r.status_code == 201, r.text
    created = r.json()
    game_id = created["game_id"]
    assert created["name"] == "FIFA 26"
    assert created["banner"] == GAME_PAYLOAD["banner"]
    assert created["game_type"] == "sports"
    assert [m["name"] for m in created["match_modes"]] == ["1 v 1", "2 v 2"]

    # Non-admins cannot use any of the admin endpoints.
    assert (await alice.post("/game/create/", json=GAME_PAYLOAD)).status_code == 403
    assert (await alice.put(f"/game/{game_id}/update/", json={"name": "Nope"})).status_code == 403
    assert (await alice.delete(f"/game/{game_id}/delete/")).status_code == 403

    # General endpoints expose the new fields.
    detail = (await client.get(f"/game/{game_id}/")).json()
    assert detail["banner"] == GAME_PAYLOAD["banner"]
    assert detail["game_type"] == "sports"
    assert len(detail["match_modes"]) == 2

    listed = (await client.get("/game/list/?platform=playstation&game_type=sports")).json()["games"]
    assert [g["id"] for g in listed] == [game_id]

    assert len((await client.get("/game/search/?q=fifa")).json()["games"]) == 1

    r = await admin.put(
        f"/game/{game_id}/update/",
        json={
            "name": "FIFA 27",
            "platform": "xbox",
            "game_type": "mmorpg",
            "match_modes": [{"name": "3 v 3", "description": "Team mode"}],
        },
    )
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["name"] == "FIFA 27"
    assert updated["platform"] == "xbox"
    assert updated["game_type"] == "mmorpg"
    assert updated["match_modes"] == [{"name": "3 v 3", "description": "Team mode"}]

    assert (await admin.delete(f"/game/{game_id}/delete/")).status_code == 200
    assert (await client.get("/game/list/")).json()["games"] == []
    assert (await client.get(f"/game/{game_id}/")).json()["is_active"] is False


async def test_game_fields_are_validated(admin):
    too_many_modes = [{"name": f"Mode {n}", "description": "X"} for n in range(4)]

    for body in [
        {**GAME_PAYLOAD, "game_type": "fps"},
        {**GAME_PAYLOAD, "match_modes": []},
        {**GAME_PAYLOAD, "match_modes": too_many_modes},
        {**GAME_PAYLOAD, "banner": "not-a-url"},
        {**GAME_PAYLOAD, "platform": "nintendo"},
    ]:
        assert (await admin.post("/game/create/", json=body)).status_code == 422


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


async def test_admin_can_upload_a_banner_and_use_it_on_a_game(client, admin, make_account):
    alice = await make_account("alice")
    files = {"file": ("banner.png", PNG_BYTES, "image/png")}

    r = await admin.post("/game/banner/upload/", files=files)
    assert r.status_code == 201, r.text
    uploaded = r.json()
    assert uploaded["banner"].startswith("/uploads/banners/")
    assert uploaded["banner"].endswith(".png")
    assert uploaded["url"].endswith(uploaded["banner"])

    # The file is served and its path is accepted when creating a game.
    assert (await client.get(uploaded["banner"])).status_code == 200
    r = await admin.post(
        "/game/create/",
        json={**GAME_PAYLOAD, "name": "Uploaded Banner Game", "banner": uploaded["banner"]},
    )
    assert r.status_code == 201, r.text
    assert r.json()["banner"] == uploaded["banner"]

    # Only admins may upload, and only real images are accepted.
    assert (await alice.post("/game/banner/upload/", files=files)).status_code == 403
    fake = {"file": ("banner.png", b"<script>alert(1)</script>", "image/png")}
    assert (await admin.post("/game/banner/upload/", files=fake)).status_code == 400
    empty = {"file": ("banner.png", b"", "image/png")}
    assert (await admin.post("/game/banner/upload/", files=empty)).status_code == 400
