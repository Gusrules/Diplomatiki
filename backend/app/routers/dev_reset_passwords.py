from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.security import hash_password
from app.models.student import Student
from app.models.teacher import Teacher

router = APIRouter(prefix="/dev", tags=["Dev"])

@router.post("/reset-passwords")
def reset_passwords(db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.email == "student@test.com").first()
    if s:
        s.password_hash = hash_password("1234")

    t = db.query(Teacher).filter(Teacher.email == "teacher@test.com").first()
    if t:
        t.password_hash = hash_password("1234")

    db.commit()
    return {"ok": True}
