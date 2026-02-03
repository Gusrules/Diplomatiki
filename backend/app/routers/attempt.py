from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.user_level import UserLevel
from app.models.card_meta import CardMeta
from datetime import date

from app.schemas.attempt import AttemptSubmit, AttemptSubmitResult, AttemptResultQuestion

from app.core.sm2 import update_difficulty_score, update_user_level

from app.schemas.attempt import (
    AttemptSubmitAnswersIn,
    AttemptSubmitAnswersResult,
    AttemptResultQuestionChoice,
)

router = APIRouter(prefix="/attempts", tags=["Attempts"])

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.db import get_db
from app.models.attempt import Attempt
from app.models.question import Question
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.user_level import UserLevel
from app.models.card_meta import CardMeta

from app.core.sm2 import update_difficulty_score, update_user_level

# NEW schemas
from app.schemas.attempt import (
    AttemptSubmitAnswersIn,
    AttemptSubmitAnswersResult,
    AttemptResultQuestionChoice,
)

router = APIRouter(prefix="/attempts", tags=["Attempts"])


@router.post("/submit-answers", response_model=AttemptSubmitAnswersResult)
def submit_quiz_attempt_answers(payload: AttemptSubmitAnswersIn, db: Session = Depends(get_db)):
    # 1) Check quiz exists
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
        # validate selected_index
        if ans.selected_index < 0 or ans.selected_index > 3:
            raise HTTPException(status_code=400, detail=f"selected_index must be 0..3 (question {ans.question_id})")

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

        # 2) grading εδώ:
        is_correct = (ans.selected_index == question.correct_index)
        quality = 1 if is_correct else 0

        # 2.1 Attempt insert
        attempt = Attempt(
            user_id=payload.user_id,
            question_id=ans.question_id,
            quiz_id=payload.quiz_id,
            is_correct=is_correct,
            response_time=ans.response_time,
        )
        db.add(attempt)

        # 2.2 Ensure CardMeta exists (review deck)
        card = (
            db.query(CardMeta)
            .filter(
                CardMeta.user_id == payload.user_id,
                CardMeta.question_id == ans.question_id,
            )
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
            )
            db.add(card)

        # 2.3 Update difficulty_score based on correctness
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
            )
        )

    # 3) Update user_level
    score_ratio = correct / total
    lvl = (
        db.query(UserLevel)
        .filter(UserLevel.user_id == payload.user_id, UserLevel.subject_id == subject_id)
        .first()
    )

    if not lvl:
        initial_level = 5.0
        new_level = update_user_level(initial_level, score_ratio)
        lvl = UserLevel(user_id=payload.user_id, subject_id=subject_id, level=new_level)
        db.add(lvl)
    else:
        lvl.level = update_user_level(lvl.level, score_ratio)

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

@router.post("/submit", response_model=AttemptSubmitResult)
def submit_quiz_attempt(payload: AttemptSubmit, db: Session = Depends(get_db)):
    # 1️⃣ Check quiz exists
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    subject_id = quiz.subject_id

    total = len(payload.answers)
    if total == 0:
        raise HTTPException(status_code=400, detail="No answers provided")

    correct = 0
    details: list[AttemptResultQuestion] = []

    # 2️⃣ Για κάθε απάντηση: Attempt + SM-2 + difficulty
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

        # Correctness
        is_correct = ans.is_correct
        quality = 1 if is_correct else 0

        # 2.1 Καταγραφή Attempt
        attempt = Attempt(
            user_id=payload.user_id,
            question_id=ans.question_id,
            quiz_id=payload.quiz_id,
            is_correct=is_correct,
            response_time=ans.response_time,
        )
        db.add(attempt)

        # 2.2 Ensure CardMeta exists (ΔΗΜΙΟΥΡΓΙΑ κάρτας για review)
        # Δεν τρέχουμε SM-2 εδώ. Αυτό γίνεται στο /review/submit.
        card = (
            db.query(CardMeta)
            .filter(
                CardMeta.user_id == payload.user_id,
                CardMeta.question_id == ans.question_id,
            )
            .first()
        )

        if not card:
            card = CardMeta(
                user_id=payload.user_id,
                question_id=ans.question_id,
                ef=2.5,
                repetitions=0,
                interval=0,
                next_review=date.today(),   # διαθέσιμη άμεσα για review
                last_quality=None,
            )
            db.add(card)

        # 2.3 Προσαρμογή δυσκολίας ερώτησης
        if question.difficulty_score is None:
            question.difficulty_score = 5.0  # default
        question.difficulty_score = update_difficulty_score(question.difficulty_score, quality)

        # 2.4 Στατιστικά για το αποτέλεσμα
        if is_correct:
            correct += 1

        details.append(
            AttemptResultQuestion(
                question_id=ans.question_id,
                is_correct=is_correct,
            )
        )

    # 3️⃣ Προσαρμογή user_level για το συγκεκριμένο μάθημα
    score_ratio = correct / total  # 0.0 - 1.0
    level_record = (
        db.query(UserLevel)
        .filter(
            UserLevel.user_id == payload.user_id,
            UserLevel.subject_id == subject_id,
        )
        .first()
    )

    if not level_record:
        # Αν δεν υπάρχει, ξεκινάμε από ένα baseline 5.0
        initial_level = 5.0
        new_level = update_user_level(initial_level, score_ratio)
        level_record = UserLevel(
            user_id=payload.user_id,
            subject_id=subject_id,
            level=new_level,
        )
        db.add(level_record)
    else:
        level_record.level = update_user_level(level_record.level, score_ratio)

    # 4️⃣ Commit όλων
    db.commit()

    score_percent = round(score_ratio * 100, 2)

    return AttemptSubmitResult(
        user_id=payload.user_id,
        quiz_id=payload.quiz_id,
        total_questions=total,
        correct_answers=correct,
        score=score_percent,
        details=details,
    )
