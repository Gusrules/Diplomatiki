from pydantic import BaseModel
from typing import List, Optional


class AssessmentQuestionOut(BaseModel):
    id: int
    subject_id: int
    module_id: Optional[int] = None
    prompt: str
    choices: List[str]

    class Config:
        from_attributes = True


class AssessmentStartOut(BaseModel):
    quiz_id: int
    questions: List[AssessmentQuestionOut]


class AssessmentAnswerIn(BaseModel):
    question_id: int
    selected_index: int
    response_time: Optional[int] = None  # ms ή seconds (ό,τι θες)


class AssessmentSubmitIn(BaseModel):
    user_id: int
    subject_id: int
    quiz_id: int
    answers: List[AssessmentAnswerIn]


class AssessmentSubmitOut(BaseModel):
    quiz_id: int
    total: int
    correct: int
    score: float          # 0.0 - 1.0
    new_level: float      # 0.0 - 10.0
