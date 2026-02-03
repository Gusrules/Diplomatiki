from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, func
from app.db_base import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # no FK -> safe even if no users table
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_enrollment_user_subject"),
    )
