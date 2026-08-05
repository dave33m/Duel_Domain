import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

STATUS_CHOICES = ("pending", "accepted", "in_progress", "completed", "cancelled", "disputed")


class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    challenger_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    opponent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=True)
    winner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    stake: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    challenger_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    challenger_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    opponent_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    rating_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    game: Mapped["Game"] = relationship()
    challenger: Mapped["Player"] = relationship(foreign_keys=[challenger_id])
    opponent: Mapped["Player | None"] = relationship(foreign_keys=[opponent_id])
    winner: Mapped["Player | None"] = relationship(foreign_keys=[winner_id])
