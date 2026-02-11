from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.subject import Subject as SubjectModel
from app.schemas.subject import SubjectCreate as SubjectCreateSchema, SubjectOut as SubjectOutSchema
from app.models.subject_teacher import SubjectTeacher as SubjectTeacherModel 
from app.schemas.subject import AssignTeacherIn
from app.models.subject_teacher import SubjectTeacher as SubjectTeacherModel
from app.core.deps import require_teacher
from app.schemas.subject import SubjectAccessUpdateIn
from app.models.session import Session as SessionModel
from datetime import datetime, timezone
import secrets


router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.post("/", response_model=SubjectOutSchema)
def create_subject(
    data: SubjectCreateSchema,
    db: Session = Depends(get_db),
    s: SessionModel = Depends(require_teacher),
):
    exists = (
        db.query(SubjectModel)
        .filter(SubjectModel.name == data.name)
        .filter(SubjectModel.deleted == False)  # noqa
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Subject already exists")

    new_subject = SubjectModel(
        name=data.name,
        description=data.description,
        deleted=False,
    )

    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)

    # ✅ auto-assign to this teacher
    rel = SubjectTeacherModel(subject_id=new_subject.id, teacher_id=s.user_id)
    db.add(rel)
    db.commit()

    return new_subject

@router.get("/", response_model=list[SubjectOutSchema])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(SubjectModel).filter(SubjectModel.deleted == False).all()  # noqa

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

@router.patch("/{subject_id}/access", response_model=SubjectOutSchema)
def update_subject_access(
    subject_id: int,
    payload: SubjectAccessUpdateIn,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    subj = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")

    mode = (payload.access_mode or "").strip().lower()
    if mode not in ("public", "private", "invite"):
        raise HTTPException(status_code=400, detail="access_mode must be public/private/invite")

    subj.access_mode = mode

    if mode == "invite":
        code = (payload.invite_code or "").strip()
        if not code:
            # αν δεν δώσουν, φτιάχνουμε
            code = secrets.token_urlsafe(6)  # ~8 chars
        subj.invite_code = code
    else:
        subj.invite_code = None

    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj

@router.delete("/{subject_id}", response_model=dict)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    s: SessionModel = Depends(require_teacher),
):
    # must be assigned to this teacher
    rel = (
        db.query(SubjectTeacherModel)
        .filter(SubjectTeacherModel.subject_id == subject_id)
        .filter(SubjectTeacherModel.teacher_id == s.user_id)
        .filter(SubjectTeacherModel.deleted == False)  # noqa
        .first()
    )
    if not rel:
        raise HTTPException(status_code=403, detail="Not allowed")

    subj = (
        db.query(SubjectModel)
        .filter(SubjectModel.id == subject_id)
        .filter(SubjectModel.deleted == False)  # noqa
        .first()
    )
    if not subj:
        raise HTTPException(status_code=404, detail="Subject not found")

    subj.deleted = True
    subj.deleted_at = datetime.now(timezone.utc)

    db.add(subj)
    db.commit()
    return {"ok": True, "id": subject_id}
