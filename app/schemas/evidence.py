from datetime import datetime
from uuid import UUID

from typing import Annotated

from pydantic import AnyUrl, BaseModel, Field, UrlConstraints

EvidenceUrl = Annotated[AnyUrl, UrlConstraints(max_length=500, allowed_schemes=["http", "https"])]


class UploadEvidenceRequest(BaseModel):
    duel_id: UUID
    evidence_url: EvidenceUrl = Field(description="http(s) link to a screenshot or video")


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
