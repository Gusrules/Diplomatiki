from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db import get_db
from app.models.module import Module as ModuleModel
from app.models.subject import Subject as SubjectModel
from app.schemas.module import ModuleOut, ModuleCreate
from app.core.deps import require_teacher

router = APIRouter(prefix="/modules", tags=["Modules"])

@router.post("/", response_model=ModuleOut)
def create_module(data: ModuleCreate, db: Session = Depends(get_db), _s = Depends(require_teacher)):
    subject = db.query(SubjectModel).filter(SubjectModel.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    m = ModuleModel(
        subject_id=data.subject_id,
        title=data.title,
        description=data.description,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("/", response_model=list[ModuleOut])
def list_modules(subject_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(ModuleModel).filter(ModuleModel.deleted == False)  # noqa

    if subject_id is not None:
        # validate subject exists
        subject = db.query(SubjectModel).filter(SubjectModel.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        q = q.filter(ModuleModel.subject_id == subject_id)

    return q.all()


@router.get("/{module_id}", response_model=ModuleOut)
def get_module(module_id: int, db: Session = Depends(get_db)):
    m = (
        db.query(ModuleModel)
        .filter(ModuleModel.id == module_id)
        .filter(ModuleModel.deleted == False)  # noqa
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Module not found")
    return m

@router.delete("/{module_id}", response_model=dict)
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    m = (
        db.query(ModuleModel)
        .filter(ModuleModel.id == module_id)
        .filter(ModuleModel.deleted == False)  # noqa
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Module not found")

    m.deleted = True
    m.deleted_at = datetime.now(timezone.utc)
    db.add(m)
    db.commit()
    return {"ok": True, "id": module_id}