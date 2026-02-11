from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.user_level import UserLevel
from app.models.card_meta import CardMeta

from app.core.sm2 import update_difficulty_score, update_user_level

from app.schemas.attempt import (
    AttemptSubmitAnswersIn,
    AttemptSubmitAnswersResult,
    AttemptResultQuestionChoice,
)
from app.models.resource import Resource
from datetime import datetime, timezone
from app.core.sm2 import sm2_update


router = APIRouter(prefix="/attempts", tags=["Attempts"])


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ensure_synced_fields(meta: CardMeta):
    # prefer new fields, fallback to legacy
    if meta.easiness_factor is None:
        meta.easiness_factor = meta.ef if meta.ef is not None else 2.5
    if meta.interval_days is None:
        meta.interval_days = meta.interval if meta.interval is not None else 0

    # mirror προς legacy
    meta.ef = meta.easiness_factor
    meta.interval = meta.interval_days


def compute_stage(meta: CardMeta) -> str:
    # Αν δεν έχει απαντηθεί ποτέ
    if meta.last_reviewed_at is None and (meta.repetitions or 0) == 0:
        return "new"
    reps = meta.repetitions or 0
    if reps >= 3:
        return "review"
    return "learning"

@router.post("/submit-answers", response_model=AttemptSubmitAnswersResult)
def submit_quiz_attempt_answers(payload: AttemptSubmitAnswersIn, db: Session = Depends(get_db)):
    # 1) quiz exists
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    subject_id = quiz.subject_id

    total = len(payload.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers provided")

    correct = 0
    details: list[AttemptResultQuestionChoice] = []

    for ans in payload.answers:
        # Validate that question belongs to this quiz
        qq = (
            db.query(QuizQuestion)
            .filter(
                QuizQuestion.quiz_id == payload.quiz_id,
                QuizQuestion.question_id == ans.question_id,
            )
            .first()
        )
        if not qq:
            raise HTTPException(
                status_code=400,
                detail=f"Question {ans.question_id} does not belong to quiz {payload.quiz_id}",
            )

        question = db.query(Question).filter(Question.id == ans.question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {ans.question_id} not found")

        # ✅ ΠΑΝΤΑ αρχικοποιούμε explanation
        explanation = None

        # explanation από resource (αν υπάρχει)
        exp = (
            db.query(Resource)
            .filter(Resource.module_id == question.module_id)
            .filter(Resource.type == "explanation")
            .filter(Resource.deleted == False)  # noqa
            .order_by(Resource.created_at.desc())
            .first()
        )
        if exp:
            explanation = exp.content

        # Validate selected_index
        choices = question.choices or []
        if not isinstance(choices, list) or len(choices) == 0:
            raise HTTPException(status_code=400, detail=f"Question {ans.question_id} has invalid choices")

        if ans.selected_index < 0 or ans.selected_index >= len(choices):
            raise HTTPException(
                status_code=400,
                detail=f"selected_index must be 0..{len(choices)-1} (question {ans.question_id})",
            )

        is_correct = (ans.selected_index == question.correct_index)
        quality = 1 if is_correct else 0

        # Attempt insert
        db.add(
            Attempt(
                user_id=payload.user_id,
                question_id=ans.question_id,
                quiz_id=payload.quiz_id,
                selected_index=ans.selected_index,
                is_correct=is_correct,
                response_time=ans.response_time,
            )
        )

        # Ensure CardMeta exists
        card = (
            db.query(CardMeta)
            .filter(CardMeta.user_id == payload.user_id, CardMeta.question_id == ans.question_id)
            .first()
        )
        if not card:
            card = CardMeta(
                user_id=payload.user_id,
                question_id=ans.question_id,
                ef=2.5,
                repetitions=0,
                interval=0,
                next_review=date.today(),
                last_quality=None,
                status="new",
            )
            db.add(card)

            # ✅ SM-2 update εδώ (ώστε τα quiz/adaptive attempts να μην μένουν "due σήμερα")
            now = datetime.now(timezone.utc)

            # sync fields (legacy/new)
            ensure_synced_fields(card)

            new_ef, new_reps, new_interval, next_review_date = sm2_update(
                ef=card.easiness_factor,
                repetitions=card.repetitions or 0,
                interval=card.interval_days or 0,
                quality=quality,
            )

            card.easiness_factor = new_ef
            card.repetitions = new_reps
            card.interval_days = new_interval

            card.last_quality = quality
            card.last_reviewed_at = now

            card.next_review = next_review_date
            card.next_review_at = datetime.combine(next_review_date, datetime.min.time(), tzinfo=timezone.utc)

            # legacy mirrors
            card.ef = card.easiness_factor
            card.interval = card.interval_days

            card.status = compute_stage(card)


        # Update difficulty_score
        if question.difficulty_score is None:
            question.difficulty_score = 5.0
        question.difficulty_score = update_difficulty_score(question.difficulty_score, quality)

        if is_correct:
            correct += 1

        details.append(
            AttemptResultQuestionChoice(
                question_id=ans.question_id,
                selected_index=ans.selected_index,
                correct_index=question.correct_index,
                is_correct=is_correct,
                explanation=explanation,
            )
        )



    # Update user_level for this subject
    score_ratio = correct / total  # 0..1
    lvl = (
        db.query(UserLevel)
        .filter(
            UserLevel.user_id == payload.user_id,
            UserLevel.subject_id == subject_id,
            UserLevel.deleted == False,  # noqa
        )
        .first()
    )

    if not lvl:
        initial_level = 5.0
        new_level = update_user_level(initial_level, score_ratio)
        lvl = UserLevel(user_id=payload.user_id, subject_id=subject_id, level=new_level)
        db.add(lvl)
    else:
        lvl.level = update_user_level(lvl.level, score_ratio)

    # Clamp to [0,10] just in case
    lvl.level = clamp(float(lvl.level), 0.0, 10.0)

    db.commit()

    score_percent = round(score_ratio * 100, 2)

    return AttemptSubmitAnswersResult(
        user_id=payload.user_id,
        quiz_id=payload.quiz_id,
        total_questions=total,
        correct_answers=correct,
        score=score_percent,
        details=details,
    )


@router.get("/debug/last-level")
def debug_last_level(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    """
    Πρόχειρο debug endpoint (βγάλε το μετά): βλέπει τι level έχεις τώρα.
    """
    lvl = (
        db.query(UserLevel)
        .filter(UserLevel.user_id == user_id, UserLevel.subject_id == subject_id, UserLevel.deleted == False)  # noqa
        .first()
    )
    return {"exists": bool(lvl), "level": lvl.level if lvl else None}
