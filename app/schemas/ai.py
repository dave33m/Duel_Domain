from typing import Any

from pydantic import BaseModel


class ChatAssistantRequest(BaseModel):
    message: str


class ChatAssistantResponse(BaseModel):
    airee: str
    message: str


class ValidateScreenshotRequest(BaseModel):
    image_url: str


class ValidateScreenshotResponse(BaseModel):
    valid: bool
    confidence: float
    detected_scores: dict[str, Any]
    message: str


class PerformanceAnalysisResponse(BaseModel):
    message: str | None = None
    recent_form: str | None = None
    win_streak: int | None = None
    recommendation: str | None = None
    insights: str | None = None
