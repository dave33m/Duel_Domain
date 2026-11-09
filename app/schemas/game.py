from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field

Platform = Literal["playstation", "xbox", "pc", "mobile"]
GameType = Literal["mmo", "rpg", "mmorpg", "sports"]


def _validate_banner(value: str) -> str:
    """Accept an http(s) URL or a path returned by the banner upload endpoint."""
    value = value.strip()
    if value.startswith("/uploads/"):
        return value
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("Banner must be an http(s) URL or an /uploads/ path")
    return value


BannerRef = Annotated[str, Field(max_length=500), AfterValidator(_validate_banner)]


class MatchModeInput(BaseModel):
    # Optional on update: return the id to keep it; a new id is assigned when omitted.
    id: UUID | None = None
    name: str = Field(min_length=1, max_length=50, examples=["1 v 1"])
    description: str = Field(min_length=1, max_length=500)


class MatchModeOut(BaseModel):
    id: str
    name: str
    description: str


class CreateGameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    platform: Platform
    banner: BannerRef = Field(description="http(s) URL or the path returned by /game/banner/upload/")
    game_type: GameType
    match_description: str | None = Field(default=None, max_length=500)
    match_modes: list[MatchModeInput] = Field(min_length=1, max_length=3)


class UpdateGameRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    platform: Platform | None = None
    banner: BannerRef | None = None
    game_type: GameType | None = None
    match_description: str | None = Field(default=None, max_length=500)
    match_modes: list[MatchModeInput] | None = Field(default=None, min_length=1, max_length=3)
    is_active: bool | None = None


class GameOut(BaseModel):
    id: str
    name: str
    platform: str
    banner: str | None
    game_type: str | None
    match_description: str | None
    match_modes: list[MatchModeOut]
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
    match_description: str | None
    match_modes: list[MatchModeOut]
    is_active: bool


class GameUpdatedResponse(BaseModel):
    message: str
    id: str
    name: str
    platform: str
    banner: str | None
    game_type: str | None
    match_description: str | None
    match_modes: list[MatchModeOut]
    is_active: bool


class GameListResponse(BaseModel):
    games: list[GameOut]


class BannerUploadResponse(BaseModel):
    message: str
    # Relative path to store on a game.
    banner: str
    # Absolute URL for previewing right after upload.
    url: str


class MessageResponse(BaseModel):
    message: str
