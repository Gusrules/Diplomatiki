from pydantic import BaseModel

class SubjectBase(BaseModel):
    name: str
    description: str | None = None

class SubjectCreate(SubjectBase):
    pass

class SubjectOut(SubjectBase):
    id: int
    access_mode: str = "public"
    invite_code: str | None = None

    class Config:
        from_attributes = True

class AssignTeacherIn(BaseModel):
    subject_id: int
    teacher_id: int

class SubjectAccessUpdateIn(BaseModel):
    access_mode: str  # public | private | invite
    invite_code: str | None = None