from pydantic import BaseModel
from typing import List


class QuizBase(BaseModel):
    subject_id: int
    module_id: int | None = None
    title: str
    type: str = "practice"   # "practice" ή "assessment"


class QuizCreate(QuizBase):
    pass


# Πληροφορία ερώτησης μέσα σε quiz (embedded)
class QuizQuestionDetail(BaseModel):
    id: int
    prompt: str
    difficulty_score: float
    # choices κρατάμε ωμά το JSON όπως είναι στο Question
    choices: List[str]
    correct_index: int


class QuizOut(QuizBase):
    id: int
    questions: List[QuizQuestionDetail] = []

    class Config:
        from_attributes = True


class QuizAddQuestions(BaseModel):
    question_ids: List[int]
