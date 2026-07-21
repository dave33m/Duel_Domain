import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.game import (
    CreateGameRequest,
    GameCreatedResponse,
    GameDetailOut,
    GameListResponse,
    MessageResponse,
    UpdateGameRequest,
    GameUpdatedResponse,
)
from app.services.game_service import GameService

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/create/", response_model=GameCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_game(body: CreateGameRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    try:
        game = await GameService.create_game(db, body.name, body.platform)
        return {"message": "Game created successfully", "game_id": str(game.id), "name": game.name, "platform": game.platform}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/list/", response_model=GameListResponse)
async def list_games(platform: str | None = Query(default=None), is_active: bool = Query(default=True), db: AsyncSession = Depends(get_db)):
    games = await GameService.list_games(db, platform, is_active)
    return {"games": [{"id": str(g.id), "name": g.name, "platform": g.platform, "is_active": g.is_active} for g in games]}


@router.get("/search/", response_model=GameListResponse)
async def search_games(q: str = Query(...), platform: str | None = Query(default=None), db: AsyncSession = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter required")
    games = await GameService.search_games(db, q, platform)
    return {"games": [{"id": str(g.id), "name": g.name, "platform": g.platform, "is_active": g.is_active} for g in games]}


@router.get("/{game_id}/", response_model=GameDetailOut)
async def get_game(game_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        game = await GameService.get_game(db, game_id)
        return {"id": str(game.id), "name": game.name, "platform": game.platform, "is_active": game.is_active, "created_at": game.created_at}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{game_id}/update/", response_model=GameUpdatedResponse)
async def update_game(game_id: uuid.UUID, body: UpdateGameRequest, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    try:
        game = await GameService.update_game(db, game_id, body.name, body.platform, body.is_active)
        return {"message": "Game updated successfully", "id": str(game.id), "name": game.name, "platform": game.platform, "is_active": game.is_active}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{game_id}/delete/", response_model=MessageResponse)
async def delete_game(game_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    try:
        return await GameService.delete_game(db, game_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
