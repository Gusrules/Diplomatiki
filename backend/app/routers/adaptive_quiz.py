from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.db import get_db
from app.models.question import Question as QuestionModel
from app.models.user_level import UserLevel as UserLevelModel
from app.models.subject import Subject as SubjectModel
from app.models.module import Module as ModuleModel
from app.models.attempt import Attempt as AttemptModel

from app.schemas.adaptive_quiz import AdaptiveQuizQuestionOut

from app.models.quiz import Quiz as QuizModel
from app.models.quiz_question import QuizQuestion as QuizQuestionModel
from app.schemas.adaptive_quiz import AdaptiveQuizSessionOut


router = APIRouter(prefix="/adaptive-quiz", tags=["Adaptive Quiz"])


@router.get("/next", response_model=list[AdaptiveQuizQuestionOut])
def get_next_questions(
    user_id: int,
    subject_id: int,
    module_id: int | None = None,
    n: int = 5,
    exclude_last_n: int = 20,   # ✅ σωστό όνομα
    db: Session = Depends(get_db),
):
    # 1) validate subject
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # 2) validate module if provided
    if module_id is not None:
        module = db.query(ModuleModel).filter(ModuleModel.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

    # 3) fetch user level (default 5.0)
    lvl = (
        db.query(UserLevelModel)
        .filter(
            UserLevelModel.user_id == user_id,
            UserLevelModel.subject_id == subject_id,
        )
        .first()
    )
    user_level = lvl.level if lvl else 5.0

    # 4) Build exclusion list from recent attempts
    recent_attempts = (
        db.query(AttemptModel.question_id)
        .filter(AttemptModel.user_id == user_id)
        .order_by(desc(AttemptModel.created_at))
        .limit(exclude_last_n)
        .all()
    )
    excluded_ids = {qid for (qid,) in recent_attempts}

    base_filters = [
        QuestionModel.subject_id == subject_id,
        QuestionModel.deleted == False,  # noqa
    ]
    if module_id is not None:
        base_filters.append(QuestionModel.module_id == module_id)

    if excluded_ids:
        base_filters.append(~QuestionModel.id.in_(excluded_ids))

    # 5) primary range
    lo = max(0.0, user_level - 1.0)
    hi = min(10.0, user_level + 1.0)

    q = (
        db.query(QuestionModel)
        .filter(*base_filters)
        .filter(and_(QuestionModel.difficulty_score >= lo, QuestionModel.difficulty_score <= hi))
        .order_by(func.random())  # ✅ τυχαία σειρά
    )
    questions = q.limit(n).all()

    # 6) fallback: widen range if not enough
    if len(questions) < n:
        lo2 = max(0.0, user_level - 2.5)
        hi2 = min(10.0, user_level + 2.5)

        q2 = (
            db.query(QuestionModel)
            .filter(*base_filters)
            .filter(and_(QuestionModel.difficulty_score >= lo2, QuestionModel.difficulty_score <= hi2))
            .order_by(func.random())
        )
        questions = q2.limit(n).all()

    # 7) last fallback: any questions in subject/module (still random, still excluding recent)
    if len(questions) < n:
        questions = (
            db.query(QuestionModel)
            .filter(*base_filters)
            .order_by(func.random())
            .limit(n)
            .all()
        )

    return questions


@router.get("/session", response_model=AdaptiveQuizSessionOut)
def create_quiz_session(
    user_id: int,
    subject_id: int,
    module_id: int | None = None,
    n: int = 5,
    exclude_last_n: int = 20,
    db: Session = Depends(get_db),
):
    # reuse the exact selection logic from /next
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if module_id is not None:
        module = db.query(ModuleModel).filter(ModuleModel.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

    lvl = (
        db.query(UserLevelModel)
        .filter(UserLevelModel.user_id == user_id, UserLevelModel.subject_id == subject_id)
        .first()
    )
    user_level = lvl.level if lvl else 5.0

    recent_attempts = (
        db.query(AttemptModel.question_id)
        .filter(AttemptModel.user_id == user_id)
        .order_by(desc(AttemptModel.created_at))
        .limit(exclude_last_n)
        .all()
    )
    excluded_ids = {qid for (qid,) in recent_attempts}

    base_filters = [QuestionModel.subject_id == subject_id, QuestionModel.deleted == False]  # noqa
    if module_id is not None:
        base_filters.append(QuestionModel.module_id == module_id)
    if excluded_ids:
        base_filters.append(~QuestionModel.id.in_(excluded_ids))

    lo = max(0.0, user_level - 1.0)
    hi = min(10.0, user_level + 1.0)

    q = (
        db.query(QuestionModel)
        .filter(*base_filters)
        .filter(and_(QuestionModel.difficulty_score >= lo, QuestionModel.difficulty_score <= hi))
        .order_by(func.random())
    )
    questions = q.limit(n).all()

    if len(questions) < n:
        lo2 = max(0.0, user_level - 2.5)
        hi2 = min(10.0, user_level + 2.5)
        q2 = (
            db.query(QuestionModel)
            .filter(*base_filters)
            .filter(and_(QuestionModel.difficulty_score >= lo2, QuestionModel.difficulty_score <= hi2))
            .order_by(func.random())
        )
        questions = q2.limit(n).all()

    if len(questions) < n:
        questions = (
            db.query(QuestionModel)
            .filter(*base_filters)
            .order_by(func.random())
            .limit(n)
            .all()
        )

    # ✅ Create a quiz session so attempts/submit-answers can validate quiz_questions
    quiz = QuizModel(
        subject_id=subject_id,
        module_id=module_id,
        title="Adaptive Quiz Session",
        type="practice",
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    order = 1
    for qu in questions:
        db.add(
            QuizQuestionModel(
                quiz_id=quiz.id,
                question_id=qu.id,
                question_order=order,
            )
        )
        order += 1

    db.commit()

    return {"quiz_id": quiz.id, "questions": questions}
