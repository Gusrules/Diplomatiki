from sqlalchemy import (
    Column, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, UniqueConstraint, String
)
from sqlalchemy.sql import func
from app.db_base import Base


class CardMeta(Base):
    __tablename__ = "card_meta"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    # Legacy fields (κρατάμε για συμβατότητα με υπάρχον DB/data)
    ef = Column(Float, default=2.5)              # Easiness Factor (legacy)
    repetitions = Column(Integer, default=0)
    interval = Column(Integer, default=0)        # days (legacy)
    next_review = Column(Date, nullable=True)    # legacy
    last_quality = Column(Integer, nullable=True)

    # New fields (preferred)
    easiness_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=0)
    next_review_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)

    correct_streak = Column(Integer, default=0)
    incorrect_streak = Column(Integer, default=0)

    # new | learning | review | due
    status = Column(String(20), nullable=False, default="new")

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_card_meta_user_question"),
    )
