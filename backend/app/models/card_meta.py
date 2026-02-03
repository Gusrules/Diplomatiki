from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.db_base import Base

class CardMeta(Base):
    __tablename__ = "card_meta"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    ef = Column(Float, default=2.5)        # Easiness Factor
    repetitions = Column(Integer, default=0)
    interval = Column(Integer, default=0)  # days
    next_review = Column(Date, nullable=True)
    last_quality = Column(Integer, nullable=True)  # 0 = λάθος, 1 = σωστό

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_card_meta_user_question"),
    )
