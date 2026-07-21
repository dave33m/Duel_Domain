from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadEvidenceRequest(BaseModel):
    duel_id: UUID
    evidence_url: str


class EvidenceUploadedResponse(BaseModel):
    message: str
    evidence_id: str


class EvidenceOut(BaseModel):
    id: str
    submitted_by: str
    evidence_url: str
    created_at: datetime


class DuelEvidenceResponse(BaseModel):
    evidence: list[EvidenceOut]


class MessageResponse(BaseModel):
    message: str
