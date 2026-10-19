from datetime import datetime

from pydantic import BaseModel

from app.schemas.auth import Username


class UpdateProfileRequest(BaseModel):
    username: Username | None = None


class PublicPlayerProfileResponse(BaseModel):
    id: str
    username: str
    wins: int
    losses: int
    rating: int
    win_rate: float
    total_matches: int
    joined: datetime


class PlayerProfileResponse(BaseModel):
    id: str
    username: str
    email: str
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


class LeaderboardEntry(BaseModel):
    rank: int
    id: str
    username: str
    rating: int
    wins: int
    losses: int
    win_rate: float


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]


class PlayerSearchResult(BaseModel):
    id: str
    username: str
    rating: int
    wins: int
    losses: int


class PlayerSearchResponse(BaseModel):
    players: list[PlayerSearchResult]
