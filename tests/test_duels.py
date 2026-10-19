import asyncio
from datetime import timedelta

from sqlalchemy import update

from app.core.time import utcnow
from app.db.session import AsyncSessionLocal
from app.models.duel import Duel
from app.services.duel_service import MAX_OPEN_CHALLENGES


async def _profile(acct) -> dict:
    return (await acct.get("/player/me/")).json()


async def _accepted_duel(challenger, opponent, game) -> str:
    r = await challenger.post("/duel/create/", json={"game_id": game})
    assert r.status_code == 201, r.text
    duel_id = r.json()["duel_id"]
    r = await opponent.post("/duel/accept/", json={"duel_id": duel_id})
    assert r.status_code == 200, r.text
    return duel_id


async def _submit(acct, duel_id, mine, theirs):
    return await acct.post("/duel/submit-result/", json={"duel_id": duel_id, "my_score": mine, "opponent_score": theirs})


async def test_matching_reports_complete_duel_and_move_ratings(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)

    r = await _submit(alice, duel_id, 3, 1)
    assert r.json()["status"] == "accepted"
    r = await _submit(bob, duel_id, 1, 3)
    assert r.json() == {"message": "Result submitted successfully", "status": "completed", "rating_change": -16}

    a, b = await _profile(alice), await _profile(bob)
    assert (a["rating"], a["wins"], a["losses"]) == (1016, 1, 0)
    assert (b["rating"], b["wins"], b["losses"]) == (984, 0, 1)

    duels = (await alice.get("/duel/my-duels/")).json()["duels"]
    assert duels[0]["rating_change"] == 16


async def test_mismatched_reports_send_duel_to_dispute(make_account, admin, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)

    await _submit(alice, duel_id, 999, 0)  # inflated claim
    r = await _submit(bob, duel_id, 2, 1)
    assert r.json()["status"] == "disputed"
    assert r.json()["rating_change"] is None

    assert (await _profile(alice))["rating"] == 1000
    disputed = (await admin.get("/dispute/list/")).json()["disputed_duels"]
    assert disputed[0]["challenger_report"] == [999, 0]
    assert disputed[0]["opponent_report"] == [1, 2]
    assert disputed[0]["dispute_reason"] == "Players reported different scores"


async def test_draw_completes_without_rating_change(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)
    await _submit(alice, duel_id, 2, 2)
    r = await _submit(bob, duel_id, 2, 2)
    assert r.json()["status"] == "completed"
    assert (await _profile(alice))["rating"] == 1000


async def test_result_rules(make_account, game):
    alice, bob, eve = await make_account("alice"), await make_account("bob"), await make_account("eve")
    duel_id = await _accepted_duel(alice, bob, game)

    assert (await _submit(eve, duel_id, 5, 0)).status_code == 400  # not a participant
    assert (await _submit(alice, duel_id, -1, 0)).status_code == 422  # out of range
    assert (await _submit(alice, duel_id, 3, 1)).status_code == 200
    assert (await _submit(alice, duel_id, 9, 0)).status_code == 400  # no resubmitting


async def test_simultaneous_reports_finalize_exactly_once(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)

    results = await asyncio.gather(_submit(alice, duel_id, 3, 1), _submit(bob, duel_id, 1, 3))
    assert all(r.status_code == 200 for r in results)

    a = await _profile(alice)
    assert (a["rating"], a["wins"]) == (1016, 1)


async def test_concurrent_accepts_only_one_wins(make_account, game):
    alice, bob, carol = await make_account("alice"), await make_account("bob"), await make_account("carol")
    duel_id = (await alice.post("/duel/create/", json={"game_id": game})).json()["duel_id"]

    results = await asyncio.gather(
        bob.post("/duel/accept/", json={"duel_id": duel_id}),
        carol.post("/duel/accept/", json={"duel_id": duel_id}),
    )
    assert sorted(r.status_code for r in results) == [200, 400]


async def test_challenger_can_cancel_pending_challenge(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = (await alice.post("/duel/create/", json={"game_id": game})).json()["duel_id"]

    assert (await bob.post(f"/duel/{duel_id}/cancel/")).status_code == 400
    assert (await alice.post(f"/duel/{duel_id}/cancel/")).status_code == 200
    assert (await bob.post("/duel/accept/", json={"duel_id": duel_id})).status_code == 400

    accepted = await _accepted_duel(alice, bob, game)
    assert (await alice.post(f"/duel/{accepted}/cancel/")).status_code == 400


async def test_open_challenge_limit_and_stake_validation(make_account, game):
    alice = await make_account("alice")
    assert (await alice.post("/duel/create/", json={"game_id": game, "stake": "-5"})).status_code == 422

    for _ in range(MAX_OPEN_CHALLENGES):
        assert (await alice.post("/duel/create/", json={"game_id": game})).status_code == 201
    assert (await alice.post("/duel/create/", json={"game_id": game})).status_code == 400


async def test_quick_match_joins_existing_challenge(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")

    first = (await alice.post("/matchmaking/quick/", json={"game_id": game})).json()
    assert first["status"] == "waiting"
    again = (await alice.post("/matchmaking/quick/", json={"game_id": game})).json()
    assert again["duel_id"] == first["duel_id"]  # no duplicate challenge

    found = (await bob.post("/matchmaking/quick/", json={"game_id": game})).json()
    assert found["status"] == "found" and found["duel_id"] == first["duel_id"]

    # Bob is now the opponent, so he can report straight away.
    assert (await _submit(bob, found["duel_id"], 1, 0)).status_code == 200


async def test_flag_dispute_and_admin_resolution_swaps_result(make_account, admin, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)
    await _submit(alice, duel_id, 3, 1)
    await _submit(bob, duel_id, 1, 3)

    r = await bob.post("/dispute/flag/", json={"duel_id": duel_id, "reason": "Alice disconnected me"})
    assert r.status_code == 200
    disputed = (await admin.get("/dispute/list/")).json()["disputed_duels"][0]
    assert disputed["dispute_reason"] == "Alice disconnected me"
    assert disputed["disputed_by"] == "bob"

    r = await admin.post("/dispute/resolve/", json={"duel_id": duel_id, "winner_id": bob.player_id})
    assert r.status_code == 200

    a, b = await _profile(alice), await _profile(bob)
    assert (a["rating"], a["wins"], a["losses"]) == (984, 0, 1)
    assert (b["rating"], b["wins"], b["losses"]) == (1016, 1, 0)


async def test_dispute_window_closes(make_account, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)
    await _submit(alice, duel_id, 3, 1)
    await _submit(bob, duel_id, 1, 3)

    async with AsyncSessionLocal() as db:
        await db.execute(update(Duel).values(completed_at=utcnow() - timedelta(days=3)))
        await db.commit()

    r = await bob.post("/dispute/flag/", json={"duel_id": duel_id, "reason": "Too late"})
    assert r.status_code == 400


async def test_admin_cancel_of_completed_duel_rolls_back_stats(make_account, admin, game):
    alice, bob = await make_account("alice"), await make_account("bob")
    duel_id = await _accepted_duel(alice, bob, game)
    await _submit(alice, duel_id, 3, 1)
    await _submit(bob, duel_id, 1, 3)

    assert (await admin.post(f"/dispute/cancel/{duel_id}/")).status_code == 200
    a, b = await _profile(alice), await _profile(bob)
    assert (a["rating"], a["wins"], b["rating"], b["losses"]) == (1000, 0, 1000, 0)
    assert (await admin.post(f"/dispute/cancel/{duel_id}/")).status_code == 400
