from pydantic import BaseModel
from typing import List, Optional

class AdaptiveQuizQuestionOut(BaseModel):
    id: int
    subject_id: int
    module_id: Optional[int] = None
    prompt: str
    choices: List[str]

    class Config:
        from_attributes = True

class AdaptiveQuizSessionOut(BaseModel):
    quiz_id: int
    questions: List[AdaptiveQuizQuestionOut]
