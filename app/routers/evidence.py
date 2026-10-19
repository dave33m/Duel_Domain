import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player, get_current_user
from app.db.session import get_db
from app.models.player import Player
from app.models.user import User
from app.schemas.evidence import (
    DuelEvidenceResponse,
    EvidenceUploadedResponse,
    MessageResponse,
    UploadEvidenceRequest,
)
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/upload/", response_model=EvidenceUploadedResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    body: UploadEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        evidence = await EvidenceService.upload_evidence(db, body.duel_id, player.id, str(body.evidence_url))
        return {"message": "Evidence uploaded successfully", "evidence_id": str(evidence.id)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/duel/{duel_id}/", response_model=DuelEvidenceResponse)
async def get_duel_evidence(
    duel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        evidence = await EvidenceService.get_duel_evidence(db, duel_id, user)
        return {"evidence": evidence}
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{evidence_id}/delete/", response_model=MessageResponse)
async def delete_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    player: Player = Depends(get_current_player),
):
    try:
        return await EvidenceService.delete_evidence(db, evidence_id, player.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
