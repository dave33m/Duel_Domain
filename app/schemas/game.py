from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Platform = Literal["playstation", "xbox", "pc", "mobile"]


class CreateGameRequest(BaseModel):
    name: str
    platform: Platform


class UpdateGameRequest(BaseModel):
    name: str | None = None
    platform: Platform | None = None
    is_active: bool | None = None


class GameOut(BaseModel):
    id: str
    name: str
    platform: str
    is_active: bool


class GameDetailOut(GameOut):
    created_at: datetime


class GameCreatedResponse(BaseModel):
    message: str
    game_id: str
    name: str
    platform: str


class GameUpdatedResponse(BaseModel):
    message: str
    id: str
    name: str
    platform: str
    is_active: bool


class GameListResponse(BaseModel):
    games: list[GameOut]


class MessageResponse(BaseModel):
    message: str
