from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCreate, Teacher as TeacherSchema
from app.core.security import hash_password

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.post("/", response_model=TeacherSchema)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):

    existing = db.query(Teacher).filter(Teacher.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use")

    new_teacher = Teacher(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    return new_teacher
