from sqlalchemy import Column, Integer, String, DateTime, func
from app.db_base import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)

    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "student" | "teacher"
    name = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
