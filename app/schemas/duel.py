from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CreateChallengeRequest(BaseModel):
    game_id: UUID
    stake: Decimal = Decimal("0")


class AcceptChallengeRequest(BaseModel):
    duel_id: UUID


class SubmitResultRequest(BaseModel):
    duel_id: UUID
    score: int


class ChallengeCreatedResponse(BaseModel):
    message: str
    duel_id: str


class ChallengeAcceptedResponse(BaseModel):
    message: str
    duel_id: str


class ResultSubmittedResponse(BaseModel):
    message: str
    status: str


class DuelSummary(BaseModel):
    id: str
    game: str
    status: str
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
