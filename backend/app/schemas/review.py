from pydantic import BaseModel
from typing import Any, Optional


class ReviewQuestionOut(BaseModel):
    question_id: int
    prompt: str
    choices: Any
    correct_index: int

    # stage: new | learning | review
    status: str

    # computed
    is_due: bool
    next_review_at: Optional[str] = None


class ReviewSubmitIn(BaseModel):
    user_id: int
    question_id: int
    quality: int  # 0=λάθος, 1=σωστό


class ReviewSubmitOut(BaseModel):
    question_id: int
    easiness_factor: float
    repetitions: int
    interval_days: int

    # stage: new | learning | review
    status: str

    # computed
    is_due: bool
    next_review_at: str | None
