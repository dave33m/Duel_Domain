from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_player, get_optional_user
from app.db.session import get_db
from app.models.player import Player
from app.models.user import User
from app.schemas.ai import (
    ChatAssistantRequest,
    ChatAssistantResponse,
    PerformanceAnalysisResponse,
    ValidateScreenshotRequest,
    ValidateScreenshotResponse,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat/", response_model=ChatAssistantResponse)
async def chat_assistant(body: ChatAssistantRequest, user: User | None = Depends(get_optional_user)):
    """Airee - AI chat assistant for Duel Domain"""
    context = {}
    if user is not None:
        context["user_id"] = str(user.id)
        context["username"] = user.username

    response = AIService.chat_assistant(body.message, context)
    return {"airee": response, "message": body.message}


@router.post("/validate-screenshot/", response_model=ValidateScreenshotResponse)
async def validate_screenshot(body: ValidateScreenshotRequest, player: Player = Depends(get_current_player)):
    """AI-powered screenshot validation using OCR"""
    return AIService.validate_screenshot(body.image_url)


@router.get("/performance/", response_model=PerformanceAnalysisResponse)
async def performance_analysis(db: AsyncSession = Depends(get_db), player: Player = Depends(get_current_player)):
    """AI-powered performance analysis"""
    player_history = []
    return AIService.analyze_performance(player_history)
