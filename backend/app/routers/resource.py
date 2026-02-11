from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.resource import Resource as ResourceModel
from app.models.module import Module as ModuleModel
from app.models.teacher import Teacher as TeacherModel
from app.schemas.resource import ResourceCreate, ResourceOut, ResourceOutDetail
from app.schemas.resource import ResourceContentUpdate
from app.core.deps import require_teacher
from datetime import datetime, timezone
from app.schemas.resource import ResourceTitleUpdate
import os
import uuid
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.file_extract import extract_text_from_file

router = APIRouter(prefix="/resources", tags=["Resources"])

UPLOAD_DIR = Path("uploads") / "resources"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {"pdf", "docx", "txt"}


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

@router.patch("/{resource_id}/title", response_model=ResourceOut)
def update_resource_title(
    resource_id: int,
    data: ResourceTitleUpdate,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    resource = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    title = (data.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title cannot be empty")

    resource.title = title
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    resource = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    resource.deleted = True
    resource.deleted_at = datetime.now(timezone.utc)
    db.add(resource)
    db.commit()
    return {"ok": True, "id": resource_id}

@router.post("/upload", response_model=ResourceOutDetail)
def upload_resource(
    module_id: int = Form(...),
    type: str = Form(...),
    title: str = Form(...),
    uploaded_by: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _s = Depends(require_teacher),
):
    # validate module
    module = db.query(ModuleModel).filter(ModuleModel.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # validate teacher (if given)
    if uploaded_by is not None:
        teacher = db.query(TeacherModel).filter(TeacherModel.id == uploaded_by).first()
        if not teacher:
            raise HTTPException(status_code=404, detail="Teacher not found")

    # validate extension
    filename = file.filename or "file"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    # unique safe filename
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = UPLOAD_DIR / safe_name

    # save file to disk
    try:
        with open(save_path, "wb") as f:
            f.write(file.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # ✅ Extract text for AI (pdf/docx/txt). If extraction fails, keep empty.
    extracted = ""
    if ext in {"pdf", "docx", "txt"}:
        extracted = extract_text_from_file(str(save_path), file_type=ext) or ""

        # limit size so DB doesn't explode (demo-friendly)
        MAX_CHARS = 60000
        if len(extracted) > MAX_CHARS:
            extracted = extracted[:MAX_CHARS] + "\n\n[TRUNCATED]"

    resource = ResourceModel(
        module_id=module_id,
        type=type,
        title=title.strip() or filename,
        file_path=str(save_path).replace("\\", "/"),
        file_type=ext if ext else "txt",
        uploaded_by=uploaded_by,
        content=extracted,  # ✅ store extracted text here
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

@router.get("/{resource_id}/download")
def download_resource(resource_id: int, db: Session = Depends(get_db)):
    res = (
        db.query(ResourceModel)
        .filter(ResourceModel.id == resource_id)
        .filter(ResourceModel.deleted == False)  # noqa
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    # reject "generated" placeholders
    if not res.file_path or res.file_path == "generated":
        raise HTTPException(status_code=400, detail="No downloadable file for this resource")

    p = Path(res.file_path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found on server")

    # download name
    ext = (res.file_type or "").strip() or p.suffix.replace(".", "")
    download_name = f"{res.title}.{ext}" if ext else res.title

    return FileResponse(
        path=str(p),
        filename=download_name,
        media_type="application/octet-stream",
    )
