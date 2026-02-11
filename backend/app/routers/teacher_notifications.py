from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.question import Question

router = APIRouter(prefix="/teacher/notifications", tags=["Teacher Notifications"])


@router.get("/summary")
def teacher_notifications_summary(db: Session = Depends(get_db)):
    pending_questions = (
        db.query(func.count(Question.id))
        .filter(Question.deleted == False)  # noqa
        .filter(Question.status == "pending")
        .scalar()
    ) or 0

    return {
        "pending_questions": int(pending_questions),
        "total": int(pending_questions),
    }
