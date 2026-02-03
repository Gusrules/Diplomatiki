from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.subject import Subject as SubjectModel
from app.schemas.subject import SubjectCreate as SubjectCreateSchema, SubjectOut as SubjectOutSchema
from app.models.subject_teacher import SubjectTeacher as SubjectTeacherModel 
from app.schemas.subject import AssignTeacherIn
from app.models.subject_teacher import SubjectTeacher as SubjectTeacherModel


router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.post("/", response_model=SubjectOutSchema)
def create_subject(data: SubjectCreateSchema, db: Session = Depends(get_db)):
    exists = db.query(SubjectModel).filter(SubjectModel.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Subject already exists")

    new_subject = SubjectModel(
        name=data.name,
        description=data.description
    )

    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return new_subject

@router.get("/", response_model=list[SubjectOutSchema])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(SubjectModel).all()

@router.get("/teacher", response_model=list[SubjectOutSchema])
def subjects_for_teacher(teacher_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(SubjectModel)
        .join(SubjectTeacherModel, SubjectTeacherModel.subject_id == SubjectModel.id)
        .filter(SubjectTeacherModel.teacher_id == teacher_id)
        .filter(SubjectTeacherModel.deleted == False)  # noqa
        .filter(SubjectModel.deleted == False)  # noqa
        .all()
    )
    return rows

@router.post("/assign-teacher", response_model=dict)
def assign_teacher(payload: AssignTeacherIn, db: Session = Depends(get_db)):
    # prevent duplicates
    exists = (
        db.query(SubjectTeacherModel)
        .filter(SubjectTeacherModel.subject_id == payload.subject_id)
        .filter(SubjectTeacherModel.teacher_id == payload.teacher_id)
        .filter(SubjectTeacherModel.deleted == False)  # noqa
        .first()
    )
    if exists:
        return {"ok": True, "already": True}

    row = SubjectTeacherModel(subject_id=payload.subject_id, teacher_id=payload.teacher_id)
    db.add(row)
    db.commit()
    return {"ok": True}
