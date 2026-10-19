async def _accepted_duel(challenger, opponent, game) -> str:
    duel_id = (await challenger.post("/duel/create/", json={"game_id": game})).json()["duel_id"]
    await opponent.post("/duel/accept/", json={"duel_id": duel_id})
    return duel_id


async def test_public_profile_hides_email(client, make_account):
    alice = await make_account("alice")
    assert (await alice.get("/player/me/")).json()["email"] == alice.email

    public = (await client.get(f"/player/{alice.player_id}/")).json()
    assert "email" not in public
    assert public["username"] == "alice"


async def test_username_change_checks_uniqueness_and_format(make_account):
    alice, _ = await make_account("alice"), await make_account("bob")
    assert (await alice.put("/player/me/update/", json={"username": "BOB"})).status_code == 400
    assert (await alice.put("/player/me/update/", json={"username": "a b"})).status_code == 422

    r = await alice.put("/player/me/update/", json={"username": "alice_2"})
    assert r.status_code == 200 and r.json()["username"] == "alice_2"


async def test_list_limits_are_bounded(client, make_account):
    alice = await make_account("alice")
    assert (await client.get("/player/leaderboard/?limit=100000")).status_code == 422
    assert (await alice.get("/matchmaking/recommended/?limit=0")).status_code == 422
    assert (await alice.get("/duel/my-duels/?limit=500")).status_code == 422


async def test_search_treats_wildcards_literally(client, make_account):
    await make_account("alice")
    assert (await client.get("/player/search/?q=%25")).json()["players"] == []
    assert len((await client.get("/player/search/?q=ali")).json()["players"]) == 1


async def test_evidence_rules(client, make_account, admin, game):
    alice, bob, eve = await make_account("alice"), await make_account("bob"), await make_account("eve")

    pending = (await alice.post("/duel/create/", json={"game_id": game})).json()["duel_id"]
    r = await alice.post("/evidence/upload/", json={"duel_id": pending, "evidence_url": "https://img.example/a.png"})
    assert r.status_code == 400  # nothing to evidence before the duel is accepted

    duel_id = await _accepted_duel(alice, bob, game)
    r = await alice.post("/evidence/upload/", json={"duel_id": duel_id, "evidence_url": "javascript:alert(1)"})
    assert r.status_code == 422

    r = await alice.post("/evidence/upload/", json={"duel_id": duel_id, "evidence_url": "https://img.example/a.png"})
    assert r.status_code == 201
    evidence_id = r.json()["evidence_id"]

    assert (await client.get(f"/evidence/duel/{duel_id}/")).status_code == 401
    assert (await eve.get(f"/evidence/duel/{duel_id}/")).status_code == 403
    assert len((await bob.get(f"/evidence/duel/{duel_id}/")).json()["evidence"]) == 1
    assert len((await admin.get(f"/evidence/duel/{duel_id}/")).json()["evidence"]) == 1

    # Once disputed, evidence is locked.
    await alice.post("/duel/submit-result/", json={"duel_id": duel_id, "my_score": 3, "opponent_score": 0})
    await bob.post("/duel/submit-result/", json={"duel_id": duel_id, "my_score": 3, "opponent_score": 0})
    assert (await alice.delete(f"/evidence/{evidence_id}/delete/")).status_code == 400


async def test_screenshot_validation_never_claims_success(make_account):
    alice = await make_account("alice")
    r = await alice.post("/ai/validate-screenshot/", json={"image_url": "https://img.example/a.png"})
    assert r.json()["valid"] is False


async def test_performance_uses_real_history(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    assert (await alice.get("/ai/performance/")).json()["message"] == "Not enough data for analysis"

    duel_id = await _accepted_duel(alice, bob, game)
    await alice.post("/duel/submit-result/", json={"duel_id": duel_id, "my_score": 2, "opponent_score": 0})
    await bob.post("/duel/submit-result/", json={"duel_id": duel_id, "my_score": 0, "opponent_score": 2})

    assert (await alice.get("/ai/performance/")).json()["win_streak"] == 1
