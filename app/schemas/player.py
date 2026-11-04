from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.core.avatars import DICEBEAR_AVATAR_PATTERN
from app.schemas.auth import Username

AvatarValue = Annotated[str, Field(pattern=DICEBEAR_AVATAR_PATTERN)]


class AvatarInfo(BaseModel):
    # Resolved for display: the chosen DiceBear path or the bundled default image.
    avatar: str
    is_dicebear_avatar: bool
    # False means the user still has to go through avatar selection.
    avatar_selected: bool


class AvatarUpdateRequest(BaseModel):
    # Null clears the selection and falls back to the default avatar.
    avatar: AvatarValue | None = None


class AvatarResponse(AvatarInfo):
    pass


class UpdateProfileRequest(BaseModel):
    username: Username | None = None
    avatar: AvatarValue | None = None


class PublicPlayerProfileResponse(AvatarInfo):
    id: str
    username: str
    wins: int
    losses: int
    rating: int
    win_rate: float
    total_matches: int
    joined: datetime


class PlayerProfileResponse(AvatarInfo):
    id: str
    username: str
    email: str
    email_verified: bool
    wins: int
    losses: int
    rating: int
    win_rate: float
    total_matches: int
    joined: datetime


class PlayerStatsResponse(BaseModel):
    wins: int
    losses: int
    total: int
    win_rate: float


class LeaderboardEntry(AvatarInfo):
    rank: int
    id: str
    username: str
    rating: int
    wins: int
    losses: int
    win_rate: float


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]


class PlayerSearchResult(AvatarInfo):
    id: str
    username: str
    rating: int
    wins: int
    losses: int


class PlayerSearchResponse(BaseModel):
    players: list[PlayerSearchResult]
