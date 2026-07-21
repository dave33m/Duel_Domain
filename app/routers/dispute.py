import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_current_player
from app.db.session import get_db
from app.models.player import Player
from app.models.user import User
from app.schemas.dispute import (
    DisputedDuelsResponse,
    FlagDisputeRequest,
    MessageResponse,
    ResolveDisputeRequest,
)
from app.services.dispute_service import DisputeService

router = APIRouter(prefix="/dispute", tags=["dispute"])


@router.post("/flag/", response_model=MessageResponse)
async def flag_dispute(
    body: FlagDisputeRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        return await DisputeService.flag_dispute(db, body.duel_id, player.id, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/list/", response_model=DisputedDuelsResponse)
async def get_disputed_duels(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    disputed = await DisputeService.get_disputed_duels(db)
    return {"disputed_duels": disputed}


@router.post("/resolve/", response_model=MessageResponse)
async def resolve_dispute(
    body: ResolveDisputeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        return await DisputeService.resolve_dispute(db, body.duel_id, body.winner_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cancel/{duel_id}/", response_model=MessageResponse)
async def cancel_duel(
    duel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        return await DisputeService.cancel_duel(db, duel_id, admin=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
