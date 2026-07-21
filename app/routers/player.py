import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player
from app.db.session import get_db
from app.models.player import Player
from app.schemas.player import (
    LeaderboardResponse,
    PlayerProfileResponse,
    PlayerSearchResponse,
    PlayerStatsResponse,
    UpdateProfileRequest,
)
from app.services.player_service import PlayerService

router = APIRouter(prefix="/player", tags=["player"])


@router.get("/me/", response_model=PlayerProfileResponse)
async def my_profile(db: AsyncSession = Depends(get_db), player: Player = Depends(get_current_player)):
    try:
        return await PlayerService.get_profile(db, player.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/leaderboard/", response_model=LeaderboardResponse)
async def leaderboard(limit: int = Query(default=50), db: AsyncSession = Depends(get_db)):
    entries = await PlayerService.get_leaderboard(db, limit)
    return {"leaderboard": entries}


@router.get("/search/", response_model=PlayerSearchResponse)
async def search_players(q: str = Query(...), db: AsyncSession = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter required")
    players = await PlayerService.search_players(db, q)
    return {"players": players}


@router.get("/me/stats/", response_model=PlayerStatsResponse)
async def my_stats(db: AsyncSession = Depends(get_db), player: Player = Depends(get_current_player)):
    try:
        return await PlayerService.get_player_stats(db, player.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/me/update/", response_model=PlayerProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        return await PlayerService.update_profile(db, player.id, body.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{player_id}/", response_model=PlayerProfileResponse)
async def get_profile(player_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await PlayerService.get_profile(db, player_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
