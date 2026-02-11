from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class PendingQuestionOut(BaseModel):
    id: int
    subject_id: int
    module_id: Optional[int]
    prompt: str
    choices: Any
    correct_index: int
    difficulty_score: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionApproveIn(BaseModel):
    difficulty_score: Optional[float] = None


class QuestionRejectIn(BaseModel):
    reason: str
