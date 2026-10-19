import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.duel import Duel
from app.models.evidence import MatchEvidence
from app.models.player import Player
from app.models.user import User

UPLOADABLE_STATUSES = ("accepted", "completed", "disputed")


class EvidenceService:
    @staticmethod
    async def upload_evidence(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, evidence_url: str) -> MatchEvidence:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise ValueError("Duel not found")

        if player_id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Player not part of this duel")

        if duel.status not in UPLOADABLE_STATUSES:
            raise ValueError("Evidence can only be added to accepted, completed or disputed duels")

        evidence = MatchEvidence(id=uuid.uuid4(), duel_id=duel.id, submitted_by_id=player_id, evidence_url=evidence_url)
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        return evidence

    @staticmethod
    async def get_duel_evidence(db: AsyncSession, duel_id: uuid.UUID, user: User) -> list[dict]:
        """Visible to the two players in the duel and to admins."""
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise LookupError("Duel not found")

        if not user.is_admin:
            player_id = (await db.execute(select(Player.id).where(Player.user_id == user.id))).scalar_one_or_none()
            if player_id not in (duel.challenger_id, duel.opponent_id):
                raise PermissionError("Only the players in this duel can view its evidence")

        result = await db.execute(
            select(MatchEvidence)
            .where(MatchEvidence.duel_id == duel.id)
            .options(selectinload(MatchEvidence.submitted_by).selectinload(Player.user))
            .order_by(MatchEvidence.created_at)
        )
        return [
            {
                "id": str(e.id),
                "submitted_by": e.submitted_by.user.username,
                "evidence_url": e.evidence_url,
                "created_at": e.created_at,
            }
            for e in result.scalars().all()
        ]

    @staticmethod
    async def delete_evidence(db: AsyncSession, evidence_id: uuid.UUID, player_id: uuid.UUID) -> dict:
        evidence = (
            await db.execute(select(MatchEvidence).where(MatchEvidence.id == evidence_id).options(selectinload(MatchEvidence.duel)))
        ).scalar_one_or_none()
        if evidence is None:
            raise ValueError("Evidence not found")

        if evidence.submitted_by_id != player_id:
            raise ValueError("Cannot delete evidence submitted by another player")

        if evidence.duel.status == "disputed":
            raise ValueError("Evidence can't be removed while the duel is under dispute")

        await db.delete(evidence)
        await db.commit()
        return {"message": "Evidence deleted successfully"}
