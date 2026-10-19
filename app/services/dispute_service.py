import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time import utcnow
from app.models.duel import Duel
from app.models.player import Player
from app.services.results import apply_result, reload, revert_result, transition

DISPUTE_WINDOW = timedelta(hours=48)


class DisputeService:
    @staticmethod
    async def flag_dispute(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, reason: str) -> dict:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise ValueError("Duel not found")

        if player_id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Player not part of this duel")

        if duel.status != "completed":
            raise ValueError("Can only dispute completed duels")

        now = utcnow()
        if duel.completed_at is not None and now - duel.completed_at > DISPUTE_WINDOW:
            raise ValueError("The dispute window for this duel has closed")

        flagged = await transition(
            db, duel_id, ("completed",),
            status="disputed", dispute_reason=reason, disputed_by_id=player_id, disputed_at=now,
        )
        if not flagged:
            raise ValueError("Can only dispute completed duels")

        await db.commit()
        return {"message": "Duel flagged for dispute resolution"}

    @staticmethod
    async def get_disputed_duels(db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(Duel)
            .where(Duel.status == "disputed")
            .options(
                selectinload(Duel.game),
                selectinload(Duel.challenger).selectinload(Player.user),
                selectinload(Duel.opponent).selectinload(Player.user),
                selectinload(Duel.winner).selectinload(Player.user),
                selectinload(Duel.disputed_by).selectinload(Player.user),
            )
            .order_by(Duel.disputed_at.desc())
        )
        duels = result.scalars().all()
        return [
            {
                "id": str(d.id),
                "game": d.game.name,
                "challenger_id": str(d.challenger_id),
                "challenger": d.challenger.user.username,
                "opponent_id": str(d.opponent_id) if d.opponent_id else None,
                "opponent": d.opponent.user.username if d.opponent else None,
                "challenger_score": d.challenger_score,
                "opponent_score": d.opponent_score,
                "challenger_report": [d.challenger_reported_challenger_score, d.challenger_reported_opponent_score],
                "opponent_report": [d.opponent_reported_challenger_score, d.opponent_reported_opponent_score],
                "winner": d.winner.user.username if d.winner else None,
                "dispute_reason": d.dispute_reason,
                "disputed_by": d.disputed_by.user.username if d.disputed_by else None,
                "disputed_at": d.disputed_at,
                "created_at": d.created_at,
                "completed_at": d.completed_at,
            }
            for d in duels
        ]

    @staticmethod
    async def resolve_dispute(
        db: AsyncSession,
        duel_id: uuid.UUID,
        winner_id: uuid.UUID | None,
        challenger_score: int | None = None,
        opponent_score: int | None = None,
    ) -> dict:
        """Sets the final outcome; a None winner records a draw."""
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None or duel.status != "disputed":
            raise ValueError("Duel not found or not disputed")

        if winner_id is not None and winner_id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Winner must be one of the duel participants")

        values = {"status": "completed"}
        if challenger_score is not None:
            values["challenger_score"] = challenger_score
        if opponent_score is not None:
            values["opponent_score"] = opponent_score

        if not await transition(db, duel_id, ("disputed",), **values):
            raise ValueError("Duel not found or not disputed")

        await revert_result(db, duel)
        await apply_result(db, await reload(db, duel_id), winner_id)
        await db.commit()
        return {"message": "Dispute resolved successfully"}

    @staticmethod
    async def cancel_duel(db: AsyncSession, duel_id: uuid.UUID) -> dict:
        """Admin cancel from any live state; a counted result is rolled back."""
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise ValueError("Duel not found")

        if not await transition(db, duel_id, ("pending", "accepted", "completed", "disputed"), status="cancelled"):
            raise ValueError("Duel is already cancelled")

        await revert_result(db, duel)
        await db.commit()
        return {"message": "Duel cancelled successfully"}
