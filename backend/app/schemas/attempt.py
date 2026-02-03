from pydantic import BaseModel
from typing import List, Optional


# ====== OLD flow (demo correct/wrong) ======
class AnswerIn(BaseModel):
    question_id: int
    is_correct: bool
    response_time: Optional[int] = None


class AttemptSubmit(BaseModel):
    user_id: int
    quiz_id: int
    answers: List[AnswerIn]


class AttemptResultQuestion(BaseModel):
    question_id: int
    is_correct: bool


class AttemptSubmitResult(BaseModel):
    user_id: int
    quiz_id: int
    total_questions: int
    correct_answers: int
    score: float  # 0-100
    details: List[AttemptResultQuestion]


# ====== NEW flow (student selects A/B/C/D index) ======
class AttemptAnswerChoiceIn(BaseModel):
    question_id: int
    selected_index: int  # 0..3
    response_time: Optional[int] = None


class AttemptSubmitAnswersIn(BaseModel):
    user_id: int
    quiz_id: int
    answers: List[AttemptAnswerChoiceIn]


class AttemptResultQuestionChoice(BaseModel):
    question_id: int
    selected_index: int
    correct_index: int
    is_correct: bool


class AttemptSubmitAnswersResult(BaseModel):
    user_id: int
    quiz_id: int
    total_questions: int
    correct_answers: int
    score: float
    details: List[AttemptResultQuestionChoice]
