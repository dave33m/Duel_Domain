import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game


class GameService:
    @staticmethod
    async def create_game(db: AsyncSession, name: str, platform: str) -> Game:
        existing = await db.execute(select(Game).where(Game.name == name, Game.platform == platform))
        if existing.scalar_one_or_none():
            raise ValueError("Game already exists for this platform")

        game = Game(id=uuid.uuid4(), name=name, platform=platform)
        db.add(game)
        await db.commit()
        await db.refresh(game)
        return game

    @staticmethod
    async def list_games(db: AsyncSession, platform: str | None = None, is_active: bool = True) -> list[Game]:
        query = select(Game).where(Game.is_active == is_active)
        if platform:
            query = query.where(Game.platform == platform)
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
        is_active: bool | None = None,
    ) -> Game:
        game = await GameService.get_game(db, game_id)
        if name:
            game.name = name
        if platform:
            game.platform = platform
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
        stmt = select(Game).where(Game.name.icontains(query), Game.is_active == True)  # noqa: E712
        if platform:
            stmt = stmt.where(Game.platform == platform)
        result = await db.execute(stmt.limit(20))
        return list(result.scalars().all())
