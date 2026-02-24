from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.question import Question
from app.models.card_meta import CardMeta
from app.schemas.review import ReviewQuestionOut, ReviewSubmitIn, ReviewSubmitOut
from app.core.sm2 import sm2_update
from sqlalchemy import func

router = APIRouter(prefix="/review", tags=["Review"])


def ensure_synced_fields(meta: CardMeta):
    """
    Κρατάμε synchronized legacy <-> new fields για να μην σπάνε παλιά σημεία.
    Προτιμάμε τα new πεδία, αλλά αν λείπουν γεμίζουμε από legacy.
    """
    if meta.easiness_factor is None:
        meta.easiness_factor = meta.ef if meta.ef is not None else 2.5
    if meta.interval_days is None:
        meta.interval_days = meta.interval if meta.interval is not None else 0

    # mirror προς legacy
    meta.ef = meta.easiness_factor
    meta.interval = meta.interval_days

    # next_review_at fallback από next_review (legacy Date)
    if meta.next_review_at is None and meta.next_review is not None:
        meta.next_review_at = datetime.combine(meta.next_review, datetime.min.time(), tzinfo=timezone.utc)

    # και το ανάποδο: legacy next_review από next_review_at
    if meta.next_review is None and meta.next_review_at is not None:
        meta.next_review = meta.next_review_at.date()


def is_due(meta: CardMeta) -> bool:
    """
    Due είναι computed κατάσταση: next_review <= today.
    Χρησιμοποιούμε πρώτα legacy next_review (Date), αλλιώς next_review_at.
    """
    today = date.today()
    if meta.next_review is not None:
        return meta.next_review <= today
    if meta.next_review_at is not None:
        # μετατρέπουμε σε date για σύγκριση με today
        return meta.next_review_at.astimezone(timezone.utc).date() <= today
    return False


def compute_stage(meta: CardMeta) -> str:
    """
    Stage (stored) είναι: new | learning | review
    Δεν επιστρέφουμε ποτέ 'due' εδώ.
    """
    # Αν δεν έχει απαντηθεί ποτέ
    if meta.last_reviewed_at is None and (meta.repetitions or 0) == 0:
        return "new"

    reps = meta.repetitions or 0

    # απλό και καθαρό: μετά από 3 σωστά θεωρείται review-stage
    if reps >= 3:
        return "review"
    return "learning"


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
        .filter(Question.deleted == False)  # noqa
        .filter(Question.status == "approved")
        .all()
    )
    qmap = {q.id: q for q in questions}

    out: list[ReviewQuestionOut] = []
    for m in metas:
        q = qmap.get(m.question_id)
        if not q:
            continue

        ensure_synced_fields(m)

        stage = m.status or compute_stage(m)  # αν έχεις παλιά rows χωρίς status
        due = is_due(m)

        out.append(
            ReviewQuestionOut(
                question_id=q.id,
                prompt=q.prompt,
                choices=q.choices,
                correct_index=q.correct_index,
                status=("due" if due else stage),
                is_due=due,
                next_review_at=m.next_review_at.isoformat() if m.next_review_at else None,
            )
        )
    return out

@router.get("/today/count")
def review_today_count(user_id: int, db: Session = Depends(get_db)):
    today = date.today()

    # Μετράμε ΜΟΝΟ due metas (ίδιο κριτήριο με /today)
    due_count = (
        db.query(func.count(CardMeta.id))
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .filter(CardMeta.next_review <= today)
        .scalar()
    )

    return {"due_today": int(due_count or 0)}


@router.get("/next", response_model=list[ReviewQuestionOut])
def review_next(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    today = date.today()

    metas = (
        db.query(CardMeta)
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .filter(CardMeta.next_review <= today)  # ✅ ADD THIS
        .order_by(CardMeta.next_review.asc())
        .limit(limit)
        .all()
    )
    ...


    if not metas:
        return []

    qids = [m.question_id for m in metas]
    questions = (
        db.query(Question)
        .filter(Question.id.in_(qids))
        .filter(Question.deleted == False)  # noqa
        .filter(Question.status == "approved")
        .all()
    )
    qmap = {q.id: q for q in questions}

    out: list[ReviewQuestionOut] = []
    for m in metas:
        q = qmap.get(m.question_id)
        if not q:
            continue

        ensure_synced_fields(m)

        stage = m.status or compute_stage(m)
        due = is_due(m)

        out.append(
            ReviewQuestionOut(
                question_id=q.id,
                prompt=q.prompt,
                choices=q.choices,
                correct_index=q.correct_index,
                status=("due" if due else stage),
                is_due=due,
                next_review_at=m.next_review_at.isoformat() if m.next_review_at else None,
            )
        )
    return out


@router.post("/submit", response_model=ReviewSubmitOut)
def review_submit(data: ReviewSubmitIn, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question or question.status != "approved":
        raise HTTPException(status_code=404, detail="Question not found")

    meta = (
        db.query(CardMeta)
        .filter(CardMeta.user_id == data.user_id, CardMeta.question_id == data.question_id)
        .first()
    )

    now = datetime.now(timezone.utc)

    if not meta:
        meta = CardMeta(
            user_id=data.user_id,
            question_id=data.question_id,
            easiness_factor=2.5,
            interval_days=0,
            next_review_at=now,  # θα διορθωθεί αμέσως μετά από SM-2
            last_reviewed_at=None,
            correct_streak=0,
            incorrect_streak=0,
            status="new",
        )
        # legacy mirrors
        meta.ef = 2.5
        meta.repetitions = 0
        meta.interval = 0
        meta.next_review = date.today()
        meta.last_quality = None

        db.add(meta)
        db.commit()
        db.refresh(meta)

    ensure_synced_fields(meta)

    new_ef, new_reps, new_interval, next_review_date = sm2_update(
        ef=meta.easiness_factor,
        repetitions=meta.repetitions or 0,
        interval=meta.interval_days or 0,
        quality=data.quality,
    )

    meta.easiness_factor = new_ef
    meta.repetitions = new_reps
    meta.interval_days = new_interval

    meta.last_quality = data.quality
    meta.last_reviewed_at = now

    # streaks
    if data.quality == 1:
        meta.correct_streak = (meta.correct_streak or 0) + 1
        meta.incorrect_streak = 0
    else:
        meta.incorrect_streak = (meta.incorrect_streak or 0) + 1
        meta.correct_streak = 0

    # next_review -> legacy (Date) είναι το source-of-truth για due
    meta.next_review = next_review_date

    # next_review_at για convenience (UTC midnight)
    meta.next_review_at = datetime.combine(next_review_date, datetime.min.time(), tzinfo=timezone.utc)

    # sync legacy numeric fields
    meta.ef = meta.easiness_factor
    meta.interval = meta.interval_days

    # STORED stage (όχι due)
    meta.status = compute_stage(meta)

    db.add(meta)
    db.commit()
    db.refresh(meta)

    due = is_due(meta)

    return ReviewSubmitOut(
        question_id=meta.question_id,
        easiness_factor=meta.easiness_factor,
        repetitions=meta.repetitions,
        interval_days=meta.interval_days,
        status=("due" if due else meta.status),
        is_due=due,
        next_review_at=meta.next_review_at.isoformat() if meta.next_review_at else None,
    )
