from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db import get_db
from app.models.question import Question as QuestionModel
from app.models.subject import Subject as SubjectModel
from app.models.module import Module as ModuleModel

from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionOutTeacher,
    QuestionOutStudent,
)

router = APIRouter(prefix="/questions", tags=["Questions"])


def _validate_question_payload(prompt: str, choices: list[str], correct_index: int):
    if not prompt or not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt cannot be empty")
    if not isinstance(choices, list) or len(choices) != 4:
        raise HTTPException(status_code=400, detail="choices must have exactly 4 items")
    if correct_index < 0 or correct_index > 3:
        raise HTTPException(status_code=400, detail="correct_index must be 0..3")


# Teacher creates question manually (default: pending)
@router.post("/", response_model=QuestionOutTeacher)
def create_question(data: QuestionCreate, db: Session = Depends(get_db)):

    subject = db.query(SubjectModel).filter(SubjectModel.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    module = db.query(ModuleModel).filter(ModuleModel.id == data.module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    _validate_question_payload(data.prompt, data.choices, data.correct_index)

    new_question = QuestionModel(
        subject_id=data.subject_id,
        module_id=data.module_id,
        difficulty_score=data.difficulty_score,
        prompt=data.prompt.strip(),
        choices=data.choices,
        correct_index=data.correct_index,
        status="pending",
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


# STUDENT: only APPROVED questions
@router.get("/module/{module_id}", response_model=list[QuestionOutStudent])
def list_questions_student(module_id: int, db: Session = Depends(get_db)):
    return (
        db.query(QuestionModel)
        .filter(QuestionModel.module_id == module_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.status == "approved")
        .all()
    )


# TEACHER: list with status filter (status=all|pending|approved|rejected)
@router.get("/module/{module_id}/teacher", response_model=list[QuestionOutTeacher])
def list_questions_teacher(module_id: int, status: str | None = "all", db: Session = Depends(get_db)):
    q = (
        db.query(QuestionModel)
        .filter(QuestionModel.module_id == module_id)
        .filter(QuestionModel.deleted == False)  # noqa
    )
    if status and status != "all":
        q = q.filter(QuestionModel.status == status)
    return q.all()


# STUDENT: by resource -> only approved
@router.get("/resource/{resource_id}", response_model=list[QuestionOutStudent])
def list_questions_by_resource_student(resource_id: int, db: Session = Depends(get_db)):
    return (
        db.query(QuestionModel)
        .filter(QuestionModel.resource_id == resource_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.status == "approved")
        .all()
    )


# TEACHER: by resource with status filter
@router.get("/resource/{resource_id}/teacher", response_model=list[QuestionOutTeacher])
def list_questions_by_resource_teacher(resource_id: int, status: str | None = "all", db: Session = Depends(get_db)):
    q = (
        db.query(QuestionModel)
        .filter(QuestionModel.resource_id == resource_id)
        .filter(QuestionModel.deleted == False)  # noqa
    )
    if status and status != "all":
        q = q.filter(QuestionModel.status == status)
    return q.all()


@router.post("/{question_id}/approve", response_model=QuestionOutTeacher)
def approve_question(question_id: int, teacher_id: int, db: Session = Depends(get_db)):
    q = (
        db.query(QuestionModel)
        .filter(QuestionModel.id == question_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    q.status = "approved"
    q.reviewed_by = teacher_id
    q.reviewed_at = func.now()
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.post("/{question_id}/reject", response_model=QuestionOutTeacher)
def reject_question(question_id: int, teacher_id: int, db: Session = Depends(get_db)):
    q = (
        db.query(QuestionModel)
        .filter(QuestionModel.id == question_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    q.status = "rejected"
    q.reviewed_by = teacher_id
    q.reviewed_at = func.now()
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.patch("/{question_id}", response_model=QuestionOutTeacher)
def edit_question(question_id: int, data: QuestionUpdate, db: Session = Depends(get_db)):
    q = (
        db.query(QuestionModel)
        .filter(QuestionModel.id == question_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .first()
    )
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    _validate_question_payload(data.prompt, data.choices, data.correct_index)

    q.prompt = data.prompt.strip()
    q.choices = data.choices
    q.correct_index = data.correct_index
    q.updated_at = func.now()

    # IMPORTANT: edit => back to pending (needs re-approval)
    q.status = "pending"

    db.add(q)
    db.commit()
    db.refresh(q)
    return q
