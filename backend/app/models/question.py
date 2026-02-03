from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db_base import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)

    resource_id = Column(Integer, nullable=True)

    difficulty_score = Column(Float, nullable=False)  # 0–10 continuous difficulty

    prompt = Column(Text, nullable=False)
    choices = Column(JSON, nullable=False)  # list[str], e.g. ["A", "B", "C", "D"]
    correct_index = Column(Integer, nullable=False)  # 0..3 (index in choices)

    status = Column(String(20), nullable=False, default="pending")  # pending|approved|rejected
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
