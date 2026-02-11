from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.question import Question
from app.schemas.question_moderation import (
    PendingQuestionOut,
    QuestionApproveIn,
    QuestionRejectIn,
)

router = APIRouter(prefix="/teacher/questions", tags=["Teacher Questions"])


@router.get("/pending", response_model=list[PendingQuestionOut])
def list_pending_questions(
    subject_id: int | None = None,
    module_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(Question)
        .filter(Question.deleted == False)  # noqa
        .filter(Question.status == "pending")
    )

    if subject_id is not None:
        q = q.filter(Question.subject_id == subject_id)
    if module_id is not None:
        q = q.filter(Question.module_id == module_id)

    return q.order_by(Question.created_at.asc()).all()


@router.post("/{question_id}/approve")
def approve_question(
    question_id: int,
    payload: QuestionApproveIn,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question or question.deleted:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.status != "pending":
        raise HTTPException(status_code=400, detail="Question is not pending")

    # προαιρετική μικρή διόρθωση difficulty
    if payload.difficulty_score is not None:
        question.difficulty_score = payload.difficulty_score

    question.status = "approved"
    db.commit()

    return {"status": "approved", "question_id": question_id}


@router.post("/{question_id}/reject")
def reject_question(
    question_id: int,
    payload: QuestionRejectIn,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question or question.deleted:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.status != "pending":
        raise HTTPException(status_code=400, detail="Question is not pending")

    question.status = "rejected"
    question.rejection_reason = payload.reason
    db.commit()

    return {"status": "rejected", "question_id": question_id}


@router.get("/flagged")
def list_flagged_questions(db: Session = Depends(get_db)):
    return (
        db.query(Question)
        .filter(Question.flagged == True)  # noqa
        .filter(Question.deleted == False)  # noqa
        .all()
    )
