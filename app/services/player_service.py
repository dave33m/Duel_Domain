import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.avatars import avatar_payload, validate_avatar
from app.models.avatar import Avatar
from app.models.player import Player
from app.models.user import User
from app.services.auth_service import username_taken


def _win_rate(wins: int, losses: int) -> float:
    total = wins + losses
    return round((wins / total * 100), 2) if total > 0 else 0


def active_players():
    """Players whose accounts are still active; deactivated users are hidden from public lists."""
    return select(Player).join(Player.user).where(User.is_active == True)  # noqa: E712


def _with_avatar(stmt):
    """Load the player's user and their avatar so profile payloads never issue extra queries."""
    return stmt.options(selectinload(Player.user).selectinload(User.avatar))


class PlayerService:
    @staticmethod
    async def _get_player(db: AsyncSession, player_id: uuid.UUID) -> Player | None:
        result = await db.execute(_with_avatar(select(Player).where(Player.id == player_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def _apply_avatar(user: User, avatar: str | None) -> None:
        """Set, replace or clear a user's avatar. Callers commit."""
        if user.avatar is None:
            user.avatar = Avatar(user_id=user.id, avatar=avatar, selected=avatar is not None)
        else:
            user.avatar.avatar = avatar
            user.avatar.selected = avatar is not None

    @staticmethod
    def _avatar_fields(player: Player) -> dict:
        stored = player.user.avatar
        return avatar_payload(
            stored.avatar if stored else None, bool(stored and stored.selected)
        )

    @staticmethod
    async def get_profile(db: AsyncSession, player_id: uuid.UUID, include_email: bool = False) -> dict:
        result = await db.execute(
            _with_avatar(active_players().where(Player.id == player_id))
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
            **PlayerService._avatar_fields(player),
        }
        if include_email:
            profile["email"] = player.user.email
            profile["email_verified"] = player.user.is_email_verified
        return profile

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        player_id: uuid.UUID,
        username: str | None = None,
        avatar: str | None = None,
        update_avatar: bool = False,
    ) -> dict:
        player = await PlayerService._get_player(db, player_id)
        if player is None:
            raise ValueError("Player not found")

        changed = False
        if username and username != player.user.username:
            if await username_taken(db, username, exclude_user_id=player.user_id):
                raise ValueError("Username already exists")
            player.user.username = username
            changed = True

        if update_avatar:
            await PlayerService._apply_avatar(
                player.user, validate_avatar(avatar) if avatar else None
            )
            changed = True

        if changed:
            await db.commit()

        return await PlayerService.get_profile(db, player_id, include_email=True)

    @staticmethod
    async def set_avatar(db: AsyncSession, player_id: uuid.UUID, avatar: str | None) -> dict:
        player = await PlayerService._get_player(db, player_id)
        if player is None:
            raise ValueError("Player not found")

        value = validate_avatar(avatar) if avatar else None
        await PlayerService._apply_avatar(player.user, value)
        await db.commit()
        return avatar_payload(value, value is not None)

    @staticmethod
    async def get_leaderboard(db: AsyncSession, limit: int = 50) -> list[dict]:
        result = await db.execute(
            _with_avatar(active_players())
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
                **PlayerService._avatar_fields(p),
            }
            for idx, p in enumerate(players)
        ]

    @staticmethod
    async def search_players(db: AsyncSession, query: str) -> list[dict]:
        result = await db.execute(
            _with_avatar(active_players().where(User.username.icontains(query, autoescape=True)))
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
                **PlayerService._avatar_fields(p),
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
