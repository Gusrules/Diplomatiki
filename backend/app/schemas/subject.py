from pydantic import BaseModel

class SubjectBase(BaseModel):
    name: str
    description: str | None = None

class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int

    class Config:
        from_attributes = True

class AssignTeacherIn(BaseModel):
    subject_id: int
    teacher_id: int
