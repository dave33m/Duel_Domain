import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.duel import Duel
from app.models.game import Game
from app.models.player import Player


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
            select(Player)
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
        pending_duels = result.scalars().all()

        if not pending_duels:
            duel = Duel(id=uuid.uuid4(), challenger_id=player.id, game_id=game.id, status="pending")
            db.add(duel)
            await db.commit()
            await db.refresh(duel)
            return {
                "message": "No matches found. Challenge created.",
                "duel_id": str(duel.id),
                "status": "waiting",
            }

        best_match = min(pending_duels, key=lambda d: abs(d.challenger.rating - player.rating))
        return {
            "message": "Match found",
            "duel_id": str(best_match.id),
            "opponent": best_match.challenger.user.username,
            "opponent_rating": best_match.challenger.rating,
            "status": "found",
        }

    @staticmethod
    async def get_recommended_opponents(db: AsyncSession, player_id: uuid.UUID, limit: int = 10) -> list[dict]:
        player = (await db.execute(select(Player).where(Player.id == player_id))).scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        result = await db.execute(
            select(Player)
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
