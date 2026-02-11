from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct

from app.db import get_db
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.question import Question
from app.models.attempt import Attempt
from app.models.resource import Resource

from app.schemas.recommendations import (
    RecommendationsOut,
    WeakModuleOut,
    RecommendedResourceOut,
    QuizRecommendationOut,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=RecommendationsOut)
def get_recommendations(
    user_id: int,
    subject_id: int,
    accuracy_threshold: float = 0.5,
    db: Session = Depends(get_db),
):
    # 1️⃣ Check enrollment
    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.user_id == user_id, Enrollment.subject_id == subject_id)
        .first()
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="User not enrolled in subject")

    # 2️⃣ Accuracy ανά module
    rows = (
        db.query(
            Module.id.label("module_id"),
            Module.title.label("module_title"),
            func.count(Attempt.id).label("attempts"),
            func.sum(case((Attempt.is_correct == True, 1), else_=0)).label("correct"),
        )
        .join(Question, Question.module_id == Module.id)
        .join(Attempt, Attempt.question_id == Question.id)
        .filter(Attempt.user_id == user_id)
        .filter(Module.subject_id == subject_id)
        .filter(Question.deleted == False)  # noqa
        .filter(Attempt.deleted == False)   # noqa
        .group_by(Module.id)
        .all()
    )

    weak_modules: list[WeakModuleOut] = []
    weak_module_ids: list[int] = []

    for r in rows:
        if not r.attempts or r.attempts == 0:
            continue
        acc = r.correct / r.attempts
        if acc < accuracy_threshold:
            weak_modules.append(
                WeakModuleOut(
                    module_id=r.module_id,
                    module_title=r.module_title,
                    accuracy=round(acc, 2),
                )
            )
            weak_module_ids.append(r.module_id)

    # 3️⃣ Προτεινόμενα resources για weak modules
    recommended_resources: list[RecommendedResourceOut] = []
    if weak_module_ids:
        res_rows = (
            db.query(Resource)
            .filter(Resource.module_id.in_(weak_module_ids))
            .filter(Resource.deleted == False)  # noqa
            .order_by(Resource.created_at.desc())
            .limit(5)
            .all()
        )

        for r in res_rows:
            recommended_resources.append(
                RecommendedResourceOut(
                    resource_id=r.id,
                    title=r.title,
                    type=r.type,
                )
            )

    # 4️⃣ Quiz recommendation
    quiz_rec = None
    if weak_module_ids:
        quiz_rec = QuizRecommendationOut(
            subject_id=subject_id,
            module_id=weak_module_ids[0],   # πιο αδύναμο module
            suggested_questions=5,
        )

    return RecommendationsOut(
        user_id=user_id,
        subject_id=subject_id,
        weak_modules=weak_modules,
        recommended_resources=recommended_resources,
        quiz_recommendation=quiz_rec,
    )
