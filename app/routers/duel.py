import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.db.session import get_db
from app.models.player import Player
from app.schemas.duel import (
    AcceptChallengeRequest,
    ChallengeAcceptedResponse,
    ChallengeCancelledResponse,
    ChallengeCreatedResponse,
    CreateChallengeRequest,
    MyDuelsResponse,
    PendingChallengesResponse,
    ResultSubmittedResponse,
    SubmitResultRequest,
)
from app.services.duel_service import DuelService

router = APIRouter(prefix="/duel", tags=["duel"])


@router.post("/create/", response_model=ChallengeCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_challenge(
    body: CreateChallengeRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        duel = await DuelService.create_challenge(db, player.id, body.game_id, body.stake)
        return {"message": "Challenge created successfully", "duel_id": str(duel.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/accept/", response_model=ChallengeAcceptedResponse)
async def accept_challenge(
    body: AcceptChallengeRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        duel = await DuelService.accept_challenge(db, body.duel_id, player.id)
        return {"message": "Challenge accepted successfully", "duel_id": str(duel.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{duel_id}/cancel/", response_model=ChallengeCancelledResponse)
async def cancel_challenge(
    duel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        duel = await DuelService.cancel_challenge(db, duel_id, player.id)
        return {"message": "Challenge cancelled", "duel_id": str(duel.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _rating_change_for(duel, player_id) -> int | None:
    """Rating change from the given player's own perspective (None if not yet decided)."""
    if duel.rating_change is None or duel.winner_id is None:
        return None
    return duel.rating_change if duel.winner_id == player_id else -duel.rating_change


@router.post("/submit-result/", response_model=ResultSubmittedResponse)
async def submit_result(
    body: SubmitResultRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        duel = await DuelService.submit_result(db, body.duel_id, player.id, body.my_score, body.opponent_score)
        return {
            "message": "Result submitted successfully",
            "status": duel.status,
            "rating_change": _rating_change_for(duel, player.id),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-duels/", response_model=MyDuelsResponse)
async def my_duels(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    duels = await DuelService.get_player_duels(db, player.id, limit, offset)
    return {
        "duels": [
            {
                "id": str(d.id),
                "game": d.game.name,
                "status": d.status,
                "rating_change": _rating_change_for(d, player.id),
                "created_at": d.created_at,
            }
            for d in duels
        ]
    }


@router.get("/pending/", response_model=PendingChallengesResponse)
async def pending_challenges(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    duels = await DuelService.get_pending_challenges(db, limit, offset)
    return {
        "challenges": [
            {
                "id": str(d.id),
                "game": d.game.name,
                "challenger": d.challenger.user.username,
                "stake": str(d.stake),
                "created_at": d.created_at,
            }
            for d in duels
        ]
    }
