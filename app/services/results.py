"""Shared rules for moving duels between states and applying their outcome to player stats.

Status changes are conditional UPDATEs (`transition`), so two concurrent requests can't both
accept, finalize or cancel the same duel. Stat changes are applied as `col = col + n` in SQL,
so concurrent duels finishing for the same player can't overwrite each other's update.
"""
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.elo import calculate_elo_change
from app.models.duel import Duel
from app.models.player import Player


async def transition(db: AsyncSession, duel_id: uuid.UUID, from_statuses: tuple[str, ...], **values) -> bool:
    """Applies `values` only if the duel is still in one of `from_statuses`. True if it was."""
    result = await db.execute(
        update(Duel)
        .where(Duel.id == duel_id, Duel.status.in_(from_statuses))
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


async def _adjust(db: AsyncSession, player_id: uuid.UUID, wins: int, losses: int, rating: int) -> None:
    await db.execute(
        update(Player)
        .where(Player.id == player_id)
        .values(wins=Player.wins + wins, losses=Player.losses + losses, rating=Player.rating + rating)
        .execution_options(synchronize_session=False)
    )


def _loser_id(duel: Duel, winner_id: uuid.UUID) -> uuid.UUID:
    return duel.opponent_id if winner_id == duel.challenger_id else duel.challenger_id


async def apply_result(db: AsyncSession, duel: Duel, winner_id: uuid.UUID | None) -> int | None:
    """Records the winner and updates both players. A None winner is a draw: no stat changes."""
    if winner_id is None:
        await db.execute(update(Duel).where(Duel.id == duel.id).values(winner_id=None, rating_change=None))
        return None

    loser_id = _loser_id(duel, winner_id)
    ratings = dict((await db.execute(select(Player.id, Player.rating).where(Player.id.in_([winner_id, loser_id])))).all())
    change = calculate_elo_change(ratings[winner_id], ratings[loser_id])

    await _adjust(db, winner_id, wins=1, losses=0, rating=change)
    await _adjust(db, loser_id, wins=0, losses=1, rating=-change)
    await db.execute(update(Duel).where(Duel.id == duel.id).values(winner_id=winner_id, rating_change=change))
    return change


async def revert_result(db: AsyncSession, duel: Duel) -> None:
    """Undoes a previously applied result (wins, losses and the exact rating points moved)."""
    if duel.winner_id is None:
        return

    change = duel.rating_change or 0
    await _adjust(db, duel.winner_id, wins=-1, losses=0, rating=-change)
    await _adjust(db, _loser_id(duel, duel.winner_id), wins=0, losses=-1, rating=change)
    await db.execute(update(Duel).where(Duel.id == duel.id).values(winner_id=None, rating_change=None))


async def reload(db: AsyncSession, duel_id: uuid.UUID) -> Duel | None:
    result = await db.execute(select(Duel).where(Duel.id == duel_id).execution_options(populate_existing=True))
    return result.scalar_one_or_none()
