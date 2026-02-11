from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db_base import Base
from sqlalchemy import Enum

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    access_mode = Column(String(20), nullable=False, default="public")  # public | private | invite
    invite_code = Column(String(32), nullable=True)  # χρησιμοποιείται όταν access_mode == invite

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
