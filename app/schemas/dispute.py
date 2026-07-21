from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FlagDisputeRequest(BaseModel):
    duel_id: UUID
    reason: str


class ResolveDisputeRequest(BaseModel):
    duel_id: UUID
    winner_id: UUID


class DisputedDuelOut(BaseModel):
    id: str
    game: str
    challenger: str
    opponent: str | None
    challenger_score: int | None
    opponent_score: int | None
    winner: str | None
    created_at: datetime
    completed_at: datetime | None


class DisputedDuelsResponse(BaseModel):
    disputed_duels: list[DisputedDuelOut]


class MessageResponse(BaseModel):
    message: str
