import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.game import Game
from app.models.user import User
from app.schemas.game import (
    BannerUploadResponse,
    CreateGameRequest,
    GameCreatedResponse,
    GameDetailOut,
    GameListResponse,
    GameType,
    GameUpdatedResponse,
    MessageResponse,
    Platform,
    UpdateGameRequest,
)
from app.services.game_service import GameService
from app.services.upload_service import UploadService

router = APIRouter(prefix="/game", tags=["game"])


def _game_fields(game: Game) -> dict:
    return {
        "name": game.name,
        "platform": game.platform,
        "banner": game.banner,
        "game_type": game.game_type,
        "match_description": game.match_description,
        "match_modes": game.match_modes or [],
        "is_active": game.is_active,
    }


@router.post("/banner/upload/", response_model=BannerUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_banner(
    request: Request,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
):
    """Upload a game banner; pass the returned `banner` path to create/update a game."""
    try:
        path = await UploadService.save_banner(file)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "message": "Banner uploaded",
        "banner": path,
        "url": f"{str(request.base_url).rstrip('/')}{path}",
    }


@router.post("/create/", response_model=GameCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    body: CreateGameRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        game = await GameService.create_game(
            db,
            body.name,
            body.platform,
            banner=str(body.banner),
            game_type=body.game_type,
            match_description=body.match_description,
            match_modes=[mode.model_dump(mode="json") for mode in body.match_modes],
        )
        return {"message": "Game created successfully", "game_id": str(game.id), **_game_fields(game)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/list/", response_model=GameListResponse)
async def list_games(
    platform: Platform | None = Query(default=None),
    game_type: GameType | None = Query(default=None),
    is_active: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
):
    games = await GameService.list_games(db, platform, game_type, is_active)
    return {"games": [{"id": str(g.id), **_game_fields(g)} for g in games]}


@router.get("/search/", response_model=GameListResponse)
async def search_games(
    q: str = Query(..., min_length=1, max_length=100),
    platform: Platform | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    games = await GameService.search_games(db, q, platform)
    return {"games": [{"id": str(g.id), **_game_fields(g)} for g in games]}


@router.get("/{game_id}/", response_model=GameDetailOut)
async def get_game(game_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        game = await GameService.get_game(db, game_id)
        return {"id": str(game.id), "created_at": game.created_at, **_game_fields(game)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{game_id}/update/", response_model=GameUpdatedResponse)
async def update_game(
    game_id: uuid.UUID,
    body: UpdateGameRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        game = await GameService.update_game(
            db,
            game_id,
            name=body.name,
            platform=body.platform,
            banner=str(body.banner) if body.banner else None,
            game_type=body.game_type,
            match_description=body.match_description,
            match_modes=[mode.model_dump(mode="json") for mode in body.match_modes] if body.match_modes is not None else None,
            is_active=body.is_active,
        )
        return {"message": "Game updated successfully", "id": str(game.id), **_game_fields(game)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{game_id}/delete/", response_model=MessageResponse)
async def delete_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        return await GameService.delete_game(db, game_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
