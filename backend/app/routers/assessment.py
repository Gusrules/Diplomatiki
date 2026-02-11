from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.subject import Subject as SubjectModel
from app.models.module import Module as ModuleModel
from app.models.question import Question as QuestionModel
from app.models.quiz import Quiz as QuizModel
from app.models.quiz_question import QuizQuestion as QuizQuestionModel
from app.models.attempt import Attempt as AttemptModel
from app.models.user_level import UserLevel as UserLevelModel

from app.schemas.assessment import (
    AssessmentStartOut,
    AssessmentSubmitIn,
    AssessmentSubmitOut,
)

router = APIRouter(prefix="/assessment", tags=["Assessment"])


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def pick_questions_with_variety(
    db: Session,
    subject_id: int,
    module_id: int | None,
    n: int,
):
    """
    Δίνει ποικιλία δυσκολίας:
    - easy: 0-3
    - medium: 3-7
    - hard: 7-10
    Αν δεν υπάρχουν αρκετές σε ένα bucket, συμπληρώνει από οτιδήποτε approved.
    """
    base_filters = [
        QuestionModel.subject_id == subject_id,
        QuestionModel.deleted == False,  # noqa
        QuestionModel.status == "approved",
    ]
    if module_id is not None:
        base_filters.append(QuestionModel.module_id == module_id)

    # split
    easy_n = n // 3
    medium_n = n // 3
    hard_n = n - easy_n - medium_n

    def q_bucket(lo: float, hi: float, k: int):
        if k <= 0:
            return []
        return (
            db.query(QuestionModel)
            .filter(*base_filters)
            .filter(QuestionModel.difficulty_score >= lo, QuestionModel.difficulty_score < hi)
            .order_by(func.random())
            .limit(k)
            .all()
        )

    easy = q_bucket(0.0, 3.0, easy_n)
    medium = q_bucket(3.0, 7.0, medium_n)
    hard = q_bucket(7.0, 10.000001, hard_n)

    selected = {q.id: q for q in (easy + medium + hard)}  # unique by id

    # Fill if not enough
    if len(selected) < n:
        remaining = n - len(selected)
        extra = (
            db.query(QuestionModel)
            .filter(*base_filters)
            .filter(~QuestionModel.id.in_(list(selected.keys())) if selected else True)
            .order_by(func.random())
            .limit(remaining)
            .all()
        )
        for q in extra:
            selected[q.id] = q

    # Return as list (randomize a bit again)
    qs = list(selected.values())
    # για να μην είναι “bucket grouped”, ξανατυχαία σειρά:
    # (αν τα θες σταθερή σειρά, βάλε sort)
    return qs


@router.get("/start", response_model=AssessmentStartOut)
def start_assessment(
    user_id: int,
    subject_id: int,
    module_id: int | None = None,
    n: int = 20,
    db: Session = Depends(get_db),
):
    # validate subject
    subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # validate module if provided
    if module_id is not None:
        module = db.query(ModuleModel).filter(ModuleModel.id == module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

    if n < 5:
        raise HTTPException(status_code=400, detail="n must be >= 5")
    if n > 50:
        raise HTTPException(status_code=400, detail="n must be <= 50")

    questions = pick_questions_with_variety(db, subject_id, module_id, n)
    if not questions:
        raise HTTPException(status_code=404, detail="No approved questions available")

    # create quiz session
    quiz = QuizModel(
        subject_id=subject_id,
        module_id=module_id,
        title="Assessment Test",
        type="assessment",
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # attach quiz_questions
    order = 1
    for q in questions:
        db.add(
            QuizQuestionModel(
                quiz_id=quiz.id,
                question_id=q.id,
                question_order=order,
                weight=1.0,
            )
        )
        order += 1
    db.commit()

    # επιστρέφουμε questions χωρίς correct_index (schema δεν το έχει)
    return {"quiz_id": quiz.id, "questions": questions}


@router.post("/submit", response_model=AssessmentSubmitOut)
def submit_assessment(payload: AssessmentSubmitIn, db: Session = Depends(get_db)):
    # validate quiz
    quiz = db.query(QuizModel).filter(QuizModel.id == payload.quiz_id).first()
    if not quiz or quiz.deleted:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.type != "assessment":
        raise HTTPException(status_code=400, detail="Quiz is not an assessment")

    if quiz.subject_id != payload.subject_id:
        raise HTTPException(status_code=400, detail="subject_id does not match quiz")

    # fetch quiz question ids
    qq_rows = (
        db.query(QuizQuestionModel)
        .filter(QuizQuestionModel.quiz_id == payload.quiz_id)
        .all()
    )
    allowed_qids = {r.question_id for r in qq_rows}
    if not allowed_qids:
        raise HTTPException(status_code=400, detail="Assessment quiz has no questions")

    # load questions map
    questions = (
        db.query(QuestionModel)
        .filter(QuestionModel.id.in_(list(allowed_qids)))
        .all()
    )
    qmap = {q.id: q for q in questions}

    total = 0
    correct = 0

    # create attempts
    for ans in payload.answers:
        if ans.question_id not in allowed_qids:
            raise HTTPException(status_code=400, detail=f"Question {ans.question_id} not in this quiz")

        q = qmap.get(ans.question_id)
        if not q:
            raise HTTPException(status_code=404, detail=f"Question {ans.question_id} not found")

        total += 1
        is_correct = (ans.selected_index == q.correct_index)
        if is_correct:
            correct += 1

        db.add(
            AttemptModel(
                user_id=payload.user_id,
                question_id=ans.question_id,
                quiz_id=payload.quiz_id,
                is_correct=is_correct,
                response_time=ans.response_time,
            )
        )

    if total == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    score = correct / total
    new_level = clamp(round(score * 10.0, 2), 0.0, 10.0)

    # upsert user_levels (user_id, subject_id unique)
    lvl = (
        db.query(UserLevelModel)
        .filter(
            UserLevelModel.user_id == payload.user_id,
            UserLevelModel.subject_id == payload.subject_id,
            UserLevelModel.deleted == False,  # noqa
        )
        .first()
    )

    if lvl:
        lvl.level = new_level
        db.add(lvl)
    else:
        lvl = UserLevelModel(
            user_id=payload.user_id,
            subject_id=payload.subject_id,
            level=new_level,
        )
        db.add(lvl)

    db.commit()

    return AssessmentSubmitOut(
        quiz_id=payload.quiz_id,
        total=total,
        correct=correct,
        score=round(score, 4),
        new_level=new_level,
    )
