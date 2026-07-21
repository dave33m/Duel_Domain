from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.db.session import get_db
from app.models.player import Player
from app.schemas.matchmaking import (
    FindOpponentsRequest,
    OpponentsResponse,
    QuickMatchRequest,
    QuickMatchResponse,
    RecommendedOpponentsResponse,
)
from app.services.matchmaking_service import MatchmakingService

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])


@router.post("/find/", response_model=OpponentsResponse)
async def find_opponents(
    body: FindOpponentsRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        opponents = await MatchmakingService.find_opponents(db, player.id, body.game_id, body.rating_range)
        return {"opponents": opponents}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/quick/", response_model=QuickMatchResponse)
async def quick_match(
    body: QuickMatchRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        return await MatchmakingService.quick_match(db, player.id, body.game_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/recommended/", response_model=RecommendedOpponentsResponse)
async def recommended_opponents(
    limit: int = Query(default=10),
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        recommended = await MatchmakingService.get_recommended_opponents(db, player.id, limit)
        return {"recommended": recommended}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
