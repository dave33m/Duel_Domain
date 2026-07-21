import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.duel import Duel
from app.models.evidence import MatchEvidence
from app.models.player import Player


class EvidenceService:
    @staticmethod
    async def upload_evidence(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, evidence_url: str) -> MatchEvidence:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if duel is None or player is None:
            raise ValueError("Invalid duel or player")

        if player.id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Player not part of this duel")

        evidence = MatchEvidence(id=uuid.uuid4(), duel_id=duel.id, submitted_by_id=player.id, evidence_url=evidence_url)
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        return evidence

    @staticmethod
    async def get_duel_evidence(db: AsyncSession, duel_id: uuid.UUID) -> list[dict]:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise ValueError("Duel not found")

        result = await db.execute(
            select(MatchEvidence)
            .where(MatchEvidence.duel_id == duel.id)
            .options(selectinload(MatchEvidence.submitted_by).selectinload(Player.user))
        )
        evidence = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "submitted_by": e.submitted_by.user.username,
                "evidence_url": e.evidence_url,
                "created_at": e.created_at,
            }
            for e in evidence
        ]

    @staticmethod
    async def delete_evidence(db: AsyncSession, evidence_id: uuid.UUID, player_id: uuid.UUID) -> dict:
        evidence = (await db.execute(select(MatchEvidence).where(MatchEvidence.id == evidence_id))).scalar_one_or_none()
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if evidence is None or player is None:
            raise ValueError("Invalid evidence or player")

        if evidence.submitted_by_id != player.id:
            raise ValueError("Cannot delete evidence submitted by another player")

        await db.delete(evidence)
        await db.commit()
        return {"message": "Evidence deleted successfully"}
