from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.resource import Resource as ResourceModel
from app.models.module import Module as ModuleModel
from app.models.teacher import Teacher as TeacherModel
from app.schemas.resource import ResourceCreate, ResourceOut, ResourceOutDetail
from app.schemas.resource import ResourceContentUpdate
from app.core.deps import require_teacher


router = APIRouter(prefix="/resources", tags=["Resources"])


@router.post("/", response_model=ResourceOutDetail)
def create_resource(data: ResourceCreate, db: Session = Depends(get_db), _s = Depends(require_teacher)):

    # 1) module υπάρχει;
    module = db.query(ModuleModel).filter(ModuleModel.id == data.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # 2) teacher υπάρχει; (αν δόθηκε)
    if data.uploaded_by is not None:
        teacher = db.query(TeacherModel).filter(TeacherModel.id == data.uploaded_by).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

    resource = ResourceModel(
        module_id=data.module_id,
        type=data.type,
        title=data.title,
        file_path=data.file_path,
        file_type=data.file_type,
        uploaded_by=data.uploaded_by,
        content=data.content,   # ✅ σημαντικό
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("/", response_model=list[ResourceOut])
def list_resources(module_id: int | None = None, db: Session = Depends(get_db)):

    q = db.query(ResourceModel).filter(ResourceModel.deleted == False)  # noqa

    if module_id is not None:
        q = q.filter(ResourceModel.module_id == module_id)

    return q.all()


@router.get("/{resource_id}", response_model=ResourceOutDetail)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    res = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
    return res


@router.patch("/{resource_id}/content", response_model=ResourceOut)
def update_resource_content(resource_id: int, data: ResourceContentUpdate, db: Session = Depends(get_db), _s = Depends(require_teacher)):
    resource = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not data.content or not data.content.strip():
        raise HTTPException(status_code=400, detail="content cannot be empty")

    resource.content = data.content
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("/{resource_id}/content")
def get_resource_content(resource_id: int, db: Session = Depends(get_db)):
    res = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"id": res.id, "type": res.type, "title": res.title, "content": res.content}
