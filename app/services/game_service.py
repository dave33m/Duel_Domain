import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game


class GameService:
    @staticmethod
    async def create_game(
        db: AsyncSession,
        name: str,
        platform: str,
        banner: str | None = None,
        game_type: str | None = None,
        match_modes: list[dict] | None = None,
    ) -> Game:
        existing = await db.execute(
            select(Game).where(
                func.lower(Game.name) == name.strip().lower(),
                Game.platform == platform,
                Game.is_active == True,  # noqa: E712
            )
        )
        if existing.scalars().first():
            raise ValueError("Game already exists for this platform")

        game = Game(
            id=uuid.uuid4(),
            name=name.strip(),
            platform=platform,
            banner=banner,
            game_type=game_type,
            match_modes=match_modes or [],
        )
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game

    @staticmethod
    async def list_games(
        db: AsyncSession,
        platform: str | None = None,
        game_type: str | None = None,
        is_active: bool = True,
    ) -> list[Game]:
        query = select(Game).where(Game.is_active == is_active)
        if platform:
            query = query.where(Game.platform == platform)
        if game_type:
            query = query.where(Game.game_type == game_type)
        result = await db.execute(query.order_by(Game.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_game(db: AsyncSession, game_id: uuid.UUID) -> Game:
        result = await db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if game is None:
            raise ValueError("Game not found")
        return game

    @staticmethod
    async def update_game(
        db: AsyncSession,
        game_id: uuid.UUID,
        name: str | None = None,
        platform: str | None = None,
        banner: str | None = None,
        game_type: str | None = None,
        match_modes: list[dict] | None = None,
        is_active: bool | None = None,
    ) -> Game:
        game = await GameService.get_game(db, game_id)
        if name:
            game.name = name.strip()
        if platform:
            game.platform = platform
        if banner:
            game.banner = banner
        if game_type:
            game.game_type = game_type
        if match_modes is not None:
            game.match_modes = match_modes
        if is_active is not None:
            game.is_active = is_active
        await db.commit()
        await db.refresh(game)
        return game

    @staticmethod
    async def delete_game(db: AsyncSession, game_id: uuid.UUID) -> dict:
        game = await GameService.get_game(db, game_id)
        game.is_active = False
        await db.commit()
        return {"message": "Game deactivated successfully"}

    @staticmethod
    async def search_games(db: AsyncSession, query: str, platform: str | None = None) -> list[Game]:
        stmt = select(Game).where(Game.name.icontains(query, autoescape=True), Game.is_active == True)  # noqa: E712
        if platform:
            stmt = stmt.where(Game.platform == platform)
        result = await db.execute(stmt.limit(20))
        return list(result.scalars().all())
