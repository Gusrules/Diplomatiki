from pydantic import BaseModel, EmailStr

class StudentBase(BaseModel):
    name: str | None = None
    email: EmailStr

class StudentCreate(StudentBase):
    password: str

class Student(StudentBase):
    id: int

    class Config:
        orm_mode = True
