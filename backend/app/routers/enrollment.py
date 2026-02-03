from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.enrollment import Enrollment
from app.models.subject import Subject as SubjectModel
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])

@router.post("/", response_model=EnrollmentOut)
def enroll(payload: EnrollmentCreate, db: Session = Depends(get_db)):
    # subject exists?
    subj = db.query(SubjectModel).filter(SubjectModel.id == payload.subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")

    # already enrolled?
    existing = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == payload.user_id, Enrollment.subject_id == payload.subject_id)
        .first()
    )
    if existing:
        return existing

    e = Enrollment(user_id=payload.user_id, subject_id=payload.subject_id)
    db.add(e)
    db.commit()
    db.refresh(e)
    return e

@router.delete("/", response_model=dict)
def unenroll(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    e = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.subject_id == subject_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    db.delete(e)
    db.commit()
    return {"ok": True}

@router.get("/my-subjects", response_model=list[int])
def my_subject_ids(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(Enrollment.subject_id).filter(Enrollment.user_id == user_id).all()
    return [r[0] for r in rows]
