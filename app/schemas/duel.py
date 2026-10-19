from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

Score = Field(ge=0, le=999)


class CreateChallengeRequest(BaseModel):
    game_id: UUID
    stake: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("99999999.99"), max_digits=10, decimal_places=2)


class AcceptChallengeRequest(BaseModel):
    duel_id: UUID


class SubmitResultRequest(BaseModel):
    """The full scoreline as the submitting player saw it."""

    duel_id: UUID
    my_score: int = Score
    opponent_score: int = Score


class ChallengeCreatedResponse(BaseModel):
    message: str
    duel_id: str


class ChallengeAcceptedResponse(BaseModel):
    message: str
    duel_id: str


class ChallengeCancelledResponse(BaseModel):
    message: str
    duel_id: str


class ResultSubmittedResponse(BaseModel):
    message: str
    status: str
    rating_change: int | None = None


class DuelSummary(BaseModel):
    id: str
    game: str
    status: str
    rating_change: int | None = None
    created_at: datetime


class MyDuelsResponse(BaseModel):
    duels: list[DuelSummary]


class PendingChallenge(BaseModel):
    id: str
    game: str
    challenger: str
    stake: str
    created_at: datetime


class PendingChallengesResponse(BaseModel):
    challenges: list[PendingChallenge]
