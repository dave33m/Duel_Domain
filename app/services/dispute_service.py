import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.duel import Duel
from app.models.player import Player


class DisputeService:
    @staticmethod
    async def flag_dispute(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, reason: str) -> dict:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if duel is None or player is None:
            raise ValueError("Invalid duel or player")

        if player.id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Player not part of this duel")

        if duel.status != "completed":
            raise ValueError("Can only dispute completed duels")

        duel.status = "disputed"
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
            )
            .order_by(Duel.created_at.desc())
        )
        duels = result.scalars().all()
        return [
            {
                "id": str(d.id),
                "game": d.game.name,
                "challenger": d.challenger.user.username,
                "opponent": d.opponent.user.username if d.opponent else None,
                "challenger_score": d.challenger_score,
                "opponent_score": d.opponent_score,
                "winner": d.winner.user.username if d.winner else None,
                "created_at": d.created_at,
                "completed_at": d.completed_at,
            }
            for d in duels
        ]

    @staticmethod
    async def resolve_dispute(db: AsyncSession, duel_id: uuid.UUID, winner_id: uuid.UUID) -> dict:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id, Duel.status == "disputed"))).scalar_one_or_none()
        winner = (await db.execute(select(Player).where(Player.id == winner_id))).scalar_one_or_none()
        if duel is None or winner is None:
            raise ValueError("Invalid duel or player")

        if winner.id not in (duel.challenger_id, duel.opponent_id):
            raise ValueError("Winner must be one of the duel participants")

        challenger = (await db.execute(select(Player).where(Player.id == duel.challenger_id))).scalar_one()
        opponent = (await db.execute(select(Player).where(Player.id == duel.opponent_id))).scalar_one()

        if duel.winner_id:
            if duel.winner_id == challenger.id:
                challenger.wins -= 1
                opponent.losses -= 1
            else:
                opponent.wins -= 1
                challenger.losses -= 1

        duel.winner_id = winner.id
        if winner.id == challenger.id:
            challenger.wins += 1
            opponent.losses += 1
        else:
            opponent.wins += 1
            challenger.losses += 1

        duel.status = "completed"
        await db.commit()
        return {"message": "Dispute resolved successfully"}

    @staticmethod
    async def cancel_duel(db: AsyncSession, duel_id: uuid.UUID, admin: bool = False) -> dict:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
        if duel is None:
            raise ValueError("Duel not found")

        if not admin and duel.status not in ("pending", "accepted"):
            raise ValueError("Can only cancel pending or accepted duels")

        duel.status = "cancelled"
        await db.commit()
        return {"message": "Duel cancelled successfully"}
