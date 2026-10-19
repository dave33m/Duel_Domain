import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.player import Player
from app.models.user import User
from app.services.auth_service import username_taken


def _win_rate(wins: int, losses: int) -> float:
    total = wins + losses
    return round((wins / total * 100), 2) if total > 0 else 0


def active_players():
    """Players whose accounts are still active; deactivated users are hidden from public lists."""
    return select(Player).join(Player.user).where(User.is_active == True)  # noqa: E712


class PlayerService:
    @staticmethod
    async def get_profile(db: AsyncSession, player_id: uuid.UUID, include_email: bool = False) -> dict:
        result = await db.execute(
            active_players().where(Player.id == player_id).options(selectinload(Player.user))
        )
        player = result.scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        profile = {
            "id": str(player.id),
            "username": player.user.username,
            "wins": player.wins,
            "losses": player.losses,
            "rating": player.rating,
            "win_rate": _win_rate(player.wins, player.losses),
            "total_matches": player.wins + player.losses,
            "joined": player.created_at,
        }
        if include_email:
            profile["email"] = player.user.email
        return profile

    @staticmethod
    async def update_profile(db: AsyncSession, player_id: uuid.UUID, username: str | None = None) -> dict:
        result = await db.execute(
            select(Player).where(Player.id == player_id).options(selectinload(Player.user))
        )
        player = result.scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        if username and username != player.user.username:
            if await username_taken(db, username, exclude_user_id=player.user_id):
                raise ValueError("Username already exists")
            player.user.username = username
            await db.commit()

        return await PlayerService.get_profile(db, player_id, include_email=True)

    @staticmethod
    async def get_leaderboard(db: AsyncSession, limit: int = 50) -> list[dict]:
        result = await db.execute(
            active_players()
            .options(selectinload(Player.user))
            .order_by(Player.rating.desc(), Player.wins.desc())
            .limit(limit)
        )
        players = result.scalars().all()
        return [
            {
                "rank": idx + 1,
                "id": str(p.id),
                "username": p.user.username,
                "rating": p.rating,
                "wins": p.wins,
                "losses": p.losses,
                "win_rate": _win_rate(p.wins, p.losses),
            }
            for idx, p in enumerate(players)
        ]

    @staticmethod
    async def search_players(db: AsyncSession, query: str) -> list[dict]:
        result = await db.execute(
            active_players()
            .where(User.username.icontains(query, autoescape=True))
            .options(selectinload(Player.user))
            .limit(20)
        )
        players = result.scalars().all()
        return [
            {
                "id": str(p.id),
                "username": p.user.username,
                "rating": p.rating,
                "wins": p.wins,
                "losses": p.losses,
            }
            for p in players
        ]

    @staticmethod
    async def get_player_stats(db: AsyncSession, player_id: uuid.UUID) -> dict:
        result = await db.execute(select(Player).where(Player.id == player_id))
        player = result.scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        total = player.wins + player.losses
        return {
            "wins": player.wins,
            "losses": player.losses,
            "total": total,
            "win_rate": _win_rate(player.wins, player.losses),
        }
