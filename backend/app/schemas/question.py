from pydantic import BaseModel
from typing import List, Optional

class QuestionCreate(BaseModel):
    subject_id: int
    module_id: int
    prompt: str
    choices: List[str]
    correct_index: int
    difficulty_score: float = 5.0

class QuestionUpdate(BaseModel):
    prompt: str
    choices: List[str]
    correct_index: int

# Student-safe (no correct_index, no difficulty)
class QuestionOutStudent(BaseModel):
    id: int
    subject_id: int
    module_id: int
    resource_id: Optional[int] = None
    prompt: str
    choices: List[str]

    class Config:
        from_attributes = True

# Teacher view includes solution + difficulty + status
class QuestionOutTeacher(QuestionOutStudent):
    difficulty_score: float
    correct_index: int
    status: str
