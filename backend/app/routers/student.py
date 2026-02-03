from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.student import Student
from app.schemas.student import StudentCreate, Student as StudentSchema
from app.models.student import Student   # SQLAlchemy model

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=StudentSchema)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_student = Student(
        name=student.name,
        email=student.email,
        password_hash=student.password,  # προσωρινά, μετά θα το κάνουμε hashed
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.get("/", response_model=list[StudentSchema])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).all()
