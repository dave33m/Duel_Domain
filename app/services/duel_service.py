import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time import utcnow
from app.models.duel import Duel
from app.models.game import Game
from app.models.player import Player
from app.services.results import apply_result, reload, transition

MAX_OPEN_CHALLENGES = 5


async def _get_duel(db: AsyncSession, duel_id: uuid.UUID) -> Duel:
    duel = (await db.execute(select(Duel).where(Duel.id == duel_id))).scalar_one_or_none()
    if duel is None:
        raise ValueError("Duel not found")
    return duel


class DuelService:
    @staticmethod
    async def create_challenge(db: AsyncSession, challenger_id: uuid.UUID, game_id: uuid.UUID, stake: Decimal = Decimal("0")) -> Duel:
        game = (await db.execute(select(Game).where(Game.id == game_id, Game.is_active == True))).scalar_one_or_none()  # noqa: E712
        if game is None:
            raise ValueError("Invalid game")

        open_count = (await db.execute(
            select(func.count()).select_from(Duel).where(Duel.challenger_id == challenger_id, Duel.status == "pending")
        )).scalar_one()
        if open_count >= MAX_OPEN_CHALLENGES:
            raise ValueError(f"You can have at most {MAX_OPEN_CHALLENGES} open challenges")

        duel = Duel(id=uuid.uuid4(), challenger_id=challenger_id, game_id=game.id, stake=stake, status="pending")
        db.add(duel)
        await db.commit()
        await db.refresh(duel)
        return duel

    @staticmethod
    async def accept_challenge(db: AsyncSession, duel_id: uuid.UUID, opponent_id: uuid.UUID) -> Duel:
        duel = await _get_duel(db, duel_id)
        if duel.challenger_id == opponent_id:
            raise ValueError("Cannot accept your own challenge")

        accepted = await transition(
            db, duel_id, ("pending",), opponent_id=opponent_id, status="accepted", accepted_at=utcnow()
        )
        if not accepted:
            raise ValueError("This challenge is no longer available")

        await db.commit()
        return await reload(db, duel_id)

    @staticmethod
    async def cancel_challenge(db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID) -> Duel:
        duel = await _get_duel(db, duel_id)
        if duel.challenger_id != player_id:
            raise ValueError("Only the challenger can cancel this challenge")

        if not await transition(db, duel_id, ("pending",), status="cancelled"):
            raise ValueError("Only pending challenges can be cancelled")

        await db.commit()
        return await reload(db, duel_id)

    @staticmethod
    async def submit_result(
        db: AsyncSession, duel_id: uuid.UUID, player_id: uuid.UUID, my_score: int, opponent_score: int
    ) -> Duel:
        duel = await _get_duel(db, duel_id)

        if player_id == duel.challenger_id:
            submitted_col, report = Duel.challenger_submitted, {
                "challenger_submitted": True,
                "challenger_reported_challenger_score": my_score,
                "challenger_reported_opponent_score": opponent_score,
            }
        elif player_id == duel.opponent_id:
            submitted_col, report = Duel.opponent_submitted, {
                "opponent_submitted": True,
                "opponent_reported_challenger_score": opponent_score,
                "opponent_reported_opponent_score": my_score,
            }
        else:
            raise ValueError("Player not part of this duel")

        if duel.status != "accepted":
            raise ValueError("Results can only be submitted for accepted duels")

        recorded = await db.execute(
            update(Duel)
            .where(Duel.id == duel_id, Duel.status == "accepted", submitted_col == False)  # noqa: E712
            .values(**report)
            .execution_options(synchronize_session=False)
        )
        if recorded.rowcount != 1:
            raise ValueError("You have already submitted a result for this duel")
        await db.commit()

        await DuelService._finalize_if_ready(db, duel_id)
        return await reload(db, duel_id)

    @staticmethod
    async def _finalize_if_ready(db: AsyncSession, duel_id: uuid.UUID) -> None:
        duel = await reload(db, duel_id)
        if not (duel.challenger_submitted and duel.opponent_submitted):
            return

        reports_match = (
            duel.challenger_reported_challenger_score == duel.opponent_reported_challenger_score
            and duel.challenger_reported_opponent_score == duel.opponent_reported_opponent_score
        )
        now = utcnow()

        if not reports_match:
            # Whichever request gets here first moves the duel on; the other finds it already done.
            if await transition(
                db, duel_id, ("accepted",),
                status="disputed", completed_at=now, disputed_at=now,
                dispute_reason="Players reported different scores",
            ):
                await db.commit()
            return

        challenger_score = duel.challenger_reported_challenger_score
        opponent_score = duel.challenger_reported_opponent_score
        if not await transition(
            db, duel_id, ("accepted",),
            status="completed", completed_at=now,
            challenger_score=challenger_score, opponent_score=opponent_score,
        ):
            return

        if challenger_score > opponent_score:
            winner_id = duel.challenger_id
        elif opponent_score > challenger_score:
            winner_id = duel.opponent_id
        else:
            winner_id = None
        await apply_result(db, duel, winner_id)
        await db.commit()

    @staticmethod
    async def get_player_duels(db: AsyncSession, player_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[Duel]:
        result = await db.execute(
            select(Duel)
            .where(or_(Duel.challenger_id == player_id, Duel.opponent_id == player_id))
            .options(selectinload(Duel.game))
            .order_by(Duel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_pending_challenges(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[Duel]:
        result = await db.execute(
            select(Duel)
            .where(Duel.status == "pending")
            .options(selectinload(Duel.game), selectinload(Duel.challenger).selectinload(Player.user))
            .order_by(Duel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
