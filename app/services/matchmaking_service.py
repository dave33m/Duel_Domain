import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time import utcnow
from app.models.duel import Duel
from app.models.game import Game
from app.models.player import Player
from app.services.player_service import active_players
from app.services.results import transition


class MatchmakingService:
    @staticmethod
    async def find_opponents(db: AsyncSession, player_id: uuid.UUID, game_id: uuid.UUID, rating_range: int = 200) -> list[dict]:
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        game = (await db.execute(select(Game).where(Game.id == game_id, Game.is_active == True))).scalar_one_or_none()  # noqa: E712
        if player is None or game is None:
            raise ValueError("Invalid player or game")

        min_rating = player.rating - rating_range
        max_rating = player.rating + rating_range

        result = await db.execute(
            active_players()
            .where(Player.rating >= min_rating, Player.rating <= max_rating, Player.id != player.id)
            .options(selectinload(Player.user))
            .limit(20)
        )
        opponents = result.scalars().all()

        return [
            {
                "id": str(p.id),
                "username": p.user.username,
                "rating": p.rating,
                "wins": p.wins,
                "losses": p.losses,
                "rating_diff": abs(p.rating - player.rating),
            }
            for p in opponents
        ]

    @staticmethod
    async def quick_match(db: AsyncSession, player_id: uuid.UUID, game_id: uuid.UUID) -> dict:
        """Joins the closest-rated open challenge for the game, or opens a new one if none is left."""
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        game = (await db.execute(select(Game).where(Game.id == game_id, Game.is_active == True))).scalar_one_or_none()  # noqa: E712
        if player is None or game is None:
            raise ValueError("Invalid player or game")

        result = await db.execute(
            select(Duel)
            .where(Duel.game_id == game.id, Duel.status == "pending", Duel.opponent_id.is_(None), Duel.challenger_id != player.id)
            .options(selectinload(Duel.challenger).selectinload(Player.user))
            .order_by(Duel.created_at.desc())
            .limit(10)
        )
        candidates = sorted(result.scalars().all(), key=lambda d: abs(d.challenger.rating - player.rating))

        # Another player may grab a candidate first; fall through to the next one if so.
        for duel in candidates:
            if await transition(db, duel.id, ("pending",), opponent_id=player.id, status="accepted", accepted_at=utcnow()):
                await db.commit()
                return {
                    "message": "Match found",
                    "duel_id": str(duel.id),
                    "opponent": duel.challenger.user.username,
                    "opponent_rating": duel.challenger.rating,
                    "status": "found",
                }

        existing = (await db.execute(
            select(Duel).where(Duel.challenger_id == player.id, Duel.game_id == game.id, Duel.status == "pending")
        )).scalars().first()
        if existing is not None:
            return {"message": "Still waiting for an opponent.", "duel_id": str(existing.id), "status": "waiting"}

        duel = Duel(id=uuid.uuid4(), challenger_id=player.id, game_id=game.id, status="pending")
        db.add(duel)
        await db.commit()
        return {"message": "No matches found. Challenge created.", "duel_id": str(duel.id), "status": "waiting"}

    @staticmethod
    async def get_recommended_opponents(db: AsyncSession, player_id: uuid.UUID, limit: int = 10) -> list[dict]:
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        result = await db.execute(
            active_players()
            .where(Player.rating >= player.rating - 100, Player.rating <= player.rating + 100, Player.id != player.id)
            .options(selectinload(Player.user))
            .order_by(func.random())
            .limit(limit)
        )
        opponents = result.scalars().all()

        return [
            {"id": str(p.id), "username": p.user.username, "rating": p.rating, "wins": p.wins, "losses": p.losses}
            for p in opponents
        ]
