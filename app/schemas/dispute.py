from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FlagDisputeRequest(BaseModel):
    duel_id: UUID
    reason: str = Field(min_length=3, max_length=500)


class ResolveDisputeRequest(BaseModel):
    duel_id: UUID
    winner_id: UUID | None = Field(default=None, description="Player id of the winner; omit for a draw")
    challenger_score: int | None = Field(default=None, ge=0, le=999)
    opponent_score: int | None = Field(default=None, ge=0, le=999)


class DisputedDuelOut(BaseModel):
    id: str
    game: str
    challenger_id: str
    challenger: str
    opponent_id: str | None
    opponent: str | None
    challenger_score: int | None
    opponent_score: int | None
    challenger_report: list[int | None]
    opponent_report: list[int | None]
    winner: str | None
    dispute_reason: str | None
    disputed_by: str | None
    disputed_at: datetime | None
    created_at: datetime
    completed_at: datetime | None


class DisputedDuelsResponse(BaseModel):
    disputed_duels: list[DisputedDuelOut]


class MessageResponse(BaseModel):
    message: str
