from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["playstation", "xbox", "pc", "mobile"]


class CreateGameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    platform: Platform


class UpdateGameRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
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
