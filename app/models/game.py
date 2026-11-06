import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

PLATFORM_CHOICES = ("playstation", "xbox", "pc", "mobile")
GAME_TYPE_CHOICES = ("mmo", "rpg", "mmorpg", "sports")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(20))
    banner: Mapped[str | None] = mapped_column(String(500), nullable=True)
    game_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # [{"name": "1 v 1", "description": "..."}]; limited to three in the API for now.
    match_modes: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
