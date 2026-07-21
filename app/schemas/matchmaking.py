from uuid import UUID

from pydantic import BaseModel


class FindOpponentsRequest(BaseModel):
    game_id: UUID
    rating_range: int = 200


class QuickMatchRequest(BaseModel):
    game_id: UUID


class OpponentOut(BaseModel):
    id: str
    username: str
    rating: int
    wins: int
    losses: int
    rating_diff: int


class OpponentsResponse(BaseModel):
    opponents: list[OpponentOut]


class QuickMatchResponse(BaseModel):
    message: str
    duel_id: str
    status: str
    opponent: str | None = None
    opponent_rating: int | None = None


class RecommendedOpponent(BaseModel):
    id: str
    username: str
    rating: int
    wins: int
    losses: int


class RecommendedOpponentsResponse(BaseModel):
    recommended: list[RecommendedOpponent]
