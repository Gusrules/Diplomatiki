from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.db import get_db
from app.models.question import Question
from app.models.attempt import Attempt

router = APIRouter(prefix="/system/questions", tags=["System Quality"])


@router.post("/auto-flag")
def auto_flag_questions(
    min_attempts: int = 20,
    max_accuracy: float = 0.2,
    db: Session = Depends(get_db),
):
    """
    Μαρκάρει ερωτήσεις με πολύ χαμηλή επιτυχία για έλεγχο.
    """
    rows = (
        db.query(
            Question.id,
            func.count(Attempt.id).label("attempts"),
            func.sum(case((Attempt.is_correct == True, 1), else_=0)).label("correct"),
        )
        .join(Attempt, Attempt.question_id == Question.id)
        .filter(Question.deleted == False)  # noqa
        .group_by(Question.id)
        .all()
    )

    flagged = 0

    for qid, attempts, correct in rows:
        if attempts < min_attempts:
            continue
        accuracy = (correct or 0) / attempts
        if accuracy < max_accuracy:
            q = db.query(Question).filter(Question.id == qid).first()
            if q and not q.flagged:
                q.flagged = True
                q.flag_reason = f"Low accuracy ({accuracy:.2f}) over {attempts} attempts"
                flagged += 1

    db.commit()
    return {"flagged_questions": flagged}
