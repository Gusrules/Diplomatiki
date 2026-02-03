from pydantic import BaseModel
from typing import List
from datetime import date


class SubjectProgressOut(BaseModel):
    subject_id: int
    subject_name: str
    level: float

    attempts_count: int
    accuracy: float          # 0..1
    due_reviews: int

    model_config = {"from_attributes": True}


class ModuleProgressOut(BaseModel):
    module_id: int
    module_title: str

    questions_total: int
    attempted_questions: int
    accuracy: float          # 0..1
    due_reviews: int

    model_config = {"from_attributes": True}


class ReviewDayCount(BaseModel):
    day: date
    count: int


class ReviewSummaryOut(BaseModel):
    due_today: int
    overdue: int
    next_7_days: List[ReviewDayCount]


class TeacherSubjectSummaryOut(BaseModel):
    subject_id: int
    subject_name: str
    unique_students: int
    attempts_count: int
    accuracy: float
    questions_total: int