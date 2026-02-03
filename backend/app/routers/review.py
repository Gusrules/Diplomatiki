from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.question import Question
from app.models.card_meta import CardMeta
from app.schemas.review import ReviewQuestionOut, ReviewSubmitIn, ReviewSubmitOut
from app.core.sm2 import sm2_update

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/today", response_model=list[ReviewQuestionOut])
def review_today(user_id: int, db: Session = Depends(get_db)):
    today = date.today()

    metas = (
        db.query(CardMeta)
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .filter(CardMeta.next_review <= today)
        .all()
    )

    if not metas:
        return []

    qids = [m.question_id for m in metas]
    questions = (
        db.query(Question)
        .filter(Question.id.in_(qids))
        .filter(Question.deleted == False) 
        .filter(Question.status == "approved")
        .all()
    )
    qmap = {q.id: q for q in questions}

    out = []
    for qid in qids:
        q = qmap.get(qid)
        if q:
            out.append(
                ReviewQuestionOut(
                    question_id=q.id,
                    prompt=q.prompt,
                    choices=q.choices,
                    correct_index=q.correct_index
                )
            )
    return out


@router.get("/next", response_model=list[ReviewQuestionOut])
def review_next(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    metas = (
        db.query(CardMeta)
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .order_by(CardMeta.next_review.asc())
        .limit(limit)
        .all()
    )

    if not metas:
        return []

    qids = [m.question_id for m in metas]
    questions = (
        db.query(Question)
        .filter(Question.id.in_(qids))
        .filter(Question.deleted == False)
        .filter(Question.status == "approved")
        .all()
    )
    qmap = {q.id: q for q in questions}

    out = []
    for qid in qids:
        q = qmap.get(qid)
        if q:
            out.append(
                ReviewQuestionOut(
                    question_id=q.id,
                    prompt=q.prompt,
                    choices=q.choices
                )
            )
    return out


@router.post("/submit", response_model=ReviewSubmitOut)
def review_submit(data: ReviewSubmitIn, db: Session = Depends(get_db)):

    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.status != "approved":
        raise HTTPException(status_code=404, detail="Question not found")

    meta = (
        db.query(CardMeta)
        .filter(CardMeta.user_id == data.user_id, CardMeta.question_id == data.question_id)
        .first()
    )

    # Αν δεν υπάρχει card_meta, δημιουργούμε default
    if not meta:
        meta = CardMeta(
            user_id=data.user_id,
            question_id=data.question_id,
            ef=2.5,
            repetitions=0,
            interval=0,
            next_review=date.today(),
            last_quality=None
        )
        db.add(meta)
        db.commit()
        db.refresh(meta)

    # Χρησιμοποιούμε το δικό σου SM-2
    new_ef, new_reps, new_interval, next_review = sm2_update(
        ef=meta.ef,
        repetitions=meta.repetitions,
        interval=meta.interval,
        quality=data.quality
    )

    meta.ef = new_ef
    meta.repetitions = new_reps
    meta.interval = new_interval
    meta.next_review = next_review
    meta.last_quality = data.quality

    db.add(meta)
    db.commit()
    db.refresh(meta)

    return ReviewSubmitOut(
        question_id=meta.question_id,
        ef=meta.ef,
        repetitions=meta.repetitions,
        interval=meta.interval,
        next_review=meta.next_review.isoformat()
    )
