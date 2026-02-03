from pydantic import BaseModel
from typing import Any

class ReviewQuestionOut(BaseModel):
    question_id: int
    prompt: str
    choices: Any
    correct_index: int

class ReviewSubmitIn(BaseModel):
    user_id: int
    question_id: int
    quality: int  # 0=λάθος, 1=σωστό

class ReviewSubmitOut(BaseModel):
    question_id: int
    ef: float
    repetitions: int
    interval: int
    next_review: str  # ISO date
