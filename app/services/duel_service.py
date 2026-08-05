import uuid
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.elo import calculate_elo_change
from app.core.time import utcnow
from app.models.duel import Duel
from app.models.game import Game
from app.models.player import Player


class DuelService:
    @staticmethod
    async def create_challenge(db: AsyncSession, challenger_id: uuid.UUID, game_id: uuid.UUID, stake: Decimal = Decimal("0")) -> Duel:
        challenger = (await db.execute(select(Player).where(Player.id == challenger_id))).scalar_one_or_none()
        game = (await db.execute(select(Game).where(Game.id == game_id, Game.is_active == True))).scalar_one_or_none()  # noqa: E712
        if challenger is None or game is None:
            raise ValueError("Invalid player or game")

        duel = Duel(id=uuid.uuid4(), challenger_id=challenger.id, game_id=game.id, stake=stake, status="pending")
        db.add(duel)
        await db.commit()
        await db.refresh(duel)
        return duel

    @staticmethod
    async def accept_challenge(db: AsyncSession, duel_id: uuid.UUID, opponent_id: uuid.UUID) -> Duel:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id, Duel.status == "pending"))).scalar_one_or_none()
        opponent = (await db.execute(select(Player).where(Player.id == opponent_id))).scalar_one_or_none()
        if duel is None or opponent is None:
            raise ValueError("Invalid duel or player")

        if duel.challenger_id == opponent.id:
            raise ValueError("Cannot accept your own challenge")

        duel.opponent_id = opponent.id
        duel.status = "accepted"
        duel.accepted_at = utcnow()
        await db.commit()
        await db.refresh(duel)
        return duel

    @staticmethod
    async def submit_result(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, score: int) -> Duel:
        duel = (await db.execute(select(Duel).where(Duel.id == duel_id, Duel.status == "accepted"))).scalar_one_or_none()
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if duel is None or player is None:
            raise ValueError("Invalid duel or player")

        if player.id == duel.challenger_id:
            duel.challenger_score = score
            duel.challenger_submitted = True
        elif player.id == duel.opponent_id:
            duel.opponent_score = score
            duel.opponent_submitted = True
        else:
            raise ValueError("Player not part of this duel")

        if duel.challenger_submitted and duel.opponent_submitted:
            challenger = (await db.execute(select(Player).where(Player.id == duel.challenger_id))).scalar_one()
            opponent = (await db.execute(select(Player).where(Player.id == duel.opponent_id))).scalar_one()

            if duel.challenger_score > duel.opponent_score:
                duel.winner_id = challenger.id
                challenger.wins += 1
                opponent.losses += 1
                duel.rating_change = calculate_elo_change(challenger.rating, opponent.rating)
                challenger.rating += duel.rating_change
                opponent.rating -= duel.rating_change
            elif duel.opponent_score > duel.challenger_score:
                duel.winner_id = opponent.id
                opponent.wins += 1
                challenger.losses += 1
                duel.rating_change = calculate_elo_change(opponent.rating, challenger.rating)
                opponent.rating += duel.rating_change
                challenger.rating -= duel.rating_change

            duel.status = "completed"
            duel.completed_at = utcnow()

        await db.commit()
        await db.refresh(duel)
        return duel

    @staticmethod
    async def get_player_duels(db: AsyncSession, player_id: uuid.UUID) -> list[Duel]:
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        result = await db.execute(
            select(Duel)
            .where(or_(Duel.challenger_id == player.id, Duel.opponent_id == player.id))
            .options(selectinload(Duel.game))
            .order_by(Duel.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pending_challenges(db: AsyncSession) -> list[Duel]:
        result = await db.execute(
            select(Duel)
            .where(Duel.status == "pending")
            .options(selectinload(Duel.game), selectinload(Duel.challenger).selectinload(Player.user))
            .order_by(Duel.created_at.desc())
        )
        return list(result.scalars().all())
