from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import hash_password
from app.models.student import Student
from app.models.teacher import Teacher

router = APIRouter(prefix="/dev", tags=["Dev"])

@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    # student
    s = db.query(Student).filter(Student.email == "student@test.com").first()
    if not s:
        s = Student(name="Student One", email="student@test.com", password_hash=hash_password("1234"))
        db.add(s)

    # teacher
    t = db.query(Teacher).filter(Teacher.email == "teacher@test.com").first()
    if not t:
        t = Teacher(name="Teacher One", email="teacher@test.com", password_hash=hash_password("1234"))
        db.add(t)

    db.commit()
    return {"ok": True}
