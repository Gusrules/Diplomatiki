from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.quiz import Quiz
from app.models.quiz_question import QuizQuestion
from app.models.subject import Subject
from app.models.module import Module
from app.models.question import Question

from app.schemas.quiz import QuizCreate, QuizOut, QuizAddQuestions, QuizQuestionDetail

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


# --------------------------
# CREATE QUIZ
# --------------------------
@router.post("/", response_model=QuizOut)
def create_quiz(data: QuizCreate, db: Session = Depends(get_db)):

    # Validate subject
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Αν δοθεί module, ελέγχουμε ότι υπάρχει
    if data.module_id is not None:
        module = db.query(Module).filter(Module.id == data.module_id).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

    quiz = Quiz(
        subject_id=data.subject_id,
        module_id=data.module_id,
        title=data.title,
        type=data.type
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    # αρχικά δεν έχει ερωτήσεις
    return QuizOut(
        id=quiz.id,
        subject_id=quiz.subject_id,
        module_id=quiz.module_id,
        title=quiz.title,
        type=quiz.type,
        questions=[]
    )


# --------------------------
# ADD QUESTIONS TO QUIZ
# --------------------------
@router.post("/{quiz_id}/add-questions")
def add_questions_to_quiz(quiz_id: int, data: QuizAddQuestions, db: Session = Depends(get_db)):

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Validate each question & add
    order = 1
    for qid in data.question_ids:
        question = db.query(Question).filter(Question.id == qid).first()
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {qid} not found")

        qq = QuizQuestion(
            quiz_id=quiz_id,
            question_id=qid,
            question_order=order
        )
        db.add(qq)
        order += 1

    db.commit()
    return {"message": "Questions added successfully"}


# --------------------------
# GET QUIZ WITH FULL QUESTION DATA
# --------------------------
@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Φέρνουμε όλες τις εγγραφές quiz_questions για αυτό το quiz
    quiz_questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).all()

    # Για κάθε quiz_question, φορτώνουμε την αντίστοιχη Question
    question_details: list[QuizQuestionDetail] = []

    for qq in quiz_questions:
        q = db.query(Question).filter(Question.id == qq.question_id).first()
        if not q:
            # αγνοούμε χαλασμένες εγγραφές αν υπάρχουν
            continue

        question_details.append(
            QuizQuestionDetail(
                id=q.id,
                prompt=q.prompt,
                difficulty_score=q.difficulty_score,
                choices=q.choices,
                correct_index=q.correct_index
            )
        )

    # Επιστρέφουμε QuizOut με embedded questions
    return QuizOut(
        id=quiz.id,
        subject_id=quiz.subject_id,
        module_id=quiz.module_id,
        title=quiz.title,
        type=quiz.type,
        questions=question_details
    )
