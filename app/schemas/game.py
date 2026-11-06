from datetime import datetime
from typing import Annotated, Literal

from pydantic import AnyUrl, BaseModel, Field, UrlConstraints

Platform = Literal["playstation", "xbox", "pc", "mobile"]
GameType = Literal["mmo", "rpg", "mmorpg", "sports"]
BannerUrl = Annotated[AnyUrl, UrlConstraints(max_length=500, allowed_schemes=["http", "https"])]


class MatchMode(BaseModel):
    name: str = Field(min_length=1, max_length=50, examples=["1 v 1"])
    description: str = Field(min_length=1, max_length=500)


class CreateGameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    platform: Platform
    banner: BannerUrl = Field(description="http(s) link to the game banner image")
    game_type: GameType
    match_modes: list[MatchMode] = Field(min_length=1, max_length=3)


class UpdateGameRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    platform: Platform | None = None
    banner: BannerUrl | None = None
    game_type: GameType | None = None
    match_modes: list[MatchMode] | None = Field(default=None, min_length=1, max_length=3)
    is_active: bool | None = None


class GameOut(BaseModel):
    id: str
    name: str
    platform: str
    banner: str | None
    game_type: str | None
    match_modes: list[MatchMode]
    is_active: bool


class GameDetailOut(GameOut):
    created_at: datetime


class GameCreatedResponse(BaseModel):
    message: str
    game_id: str
    name: str
    platform: str
    banner: str | None
    game_type: str | None
    match_modes: list[MatchMode]
    is_active: bool


class GameUpdatedResponse(BaseModel):
    message: str
    id: str
    name: str
    platform: str
    banner: str | None
    game_type: str | None
    match_modes: list[MatchMode]
    is_active: bool


class GameListResponse(BaseModel):
    games: list[GameOut]


class MessageResponse(BaseModel):
    message: str
