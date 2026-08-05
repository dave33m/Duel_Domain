from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.db.session import get_db
from app.models.player import Player
from app.schemas.duel import (
    AcceptChallengeRequest,
    ChallengeAcceptedResponse,
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
        duel = await DuelService.submit_result(db, body.duel_id, player.id, body.score)
        return {
            "message": "Result submitted successfully",
            "status": duel.status,
            "rating_change": _rating_change_for(duel, player.id),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-duels/", response_model=MyDuelsResponse)
async def my_duels(db: AsyncSession = Depends(get_db), player: Player = Depends(get_current_player)):
    try:
        duels = await DuelService.get_player_duels(db, player.id)
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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pending/", response_model=PendingChallengesResponse)
async def pending_challenges(db: AsyncSession = Depends(get_db)):
    duels = await DuelService.get_pending_challenges(db)
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
