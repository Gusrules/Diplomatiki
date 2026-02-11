from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, event
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db_base import Base

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(100), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship (backref from Subject not required yet)
    # Questions, Resources, etc. will connect here later

