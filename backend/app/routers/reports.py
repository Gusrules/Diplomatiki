from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct, desc

from app.db import get_db
from app.models.subject import Subject as SubjectModel
from app.models.module import Module as ModuleModel
from app.models.question import Question as QuestionModel
from app.models.attempt import Attempt as AttemptModel
from app.models.user_level import UserLevel as UserLevelModel
from app.models.card_meta import CardMeta as CardMetaModel
from datetime import datetime, timedelta

from app.schemas.reports import (
    SubjectProgressOut,
    ModuleProgressOut,
    ReviewSummaryOut,
    ReviewDayCount,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/student/{user_id}/subjects", response_model=list[SubjectProgressOut])
def student_subjects_progress(user_id: int, db: Session = Depends(get_db)):
    today = date.today()

    # Όλα τα active subjects
    subjects = (
        db.query(SubjectModel)
        .filter(SubjectModel.deleted == False)  # noqa
        .all()
    )
    if not subjects:
        return []

    subject_ids = [s.id for s in subjects]

    # 1) attempts per subject + accuracy (join attempts->questions)
    attempts_agg = (
        db.query(
            QuestionModel.subject_id.label("subject_id"),
            func.count(AttemptModel.id).label("attempts_count"),
            func.sum(case((AttemptModel.is_correct == True, 1), else_=0)).label("correct_count"),
        )
        .join(QuestionModel, QuestionModel.id == AttemptModel.question_id)
        .filter(AttemptModel.user_id == user_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.subject_id.in_(subject_ids))
        .group_by(QuestionModel.subject_id)
        .all()
    )
    attempts_map = {row.subject_id: row for row in attempts_agg}

    # 2) due reviews per subject (card_meta->questions)
    due_reviews_agg = (
        db.query(
            QuestionModel.subject_id.label("subject_id"),
            func.count(CardMetaModel.id).label("due_reviews"),
        )
        .join(QuestionModel, QuestionModel.id == CardMetaModel.question_id)
        .filter(CardMetaModel.user_id == user_id)
        .filter(CardMetaModel.deleted == False)  # noqa
        .filter(CardMetaModel.next_review != None)  # noqa
        .filter(CardMetaModel.next_review <= today)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.subject_id.in_(subject_ids))
        .group_by(QuestionModel.subject_id)
        .all()
    )
    due_map = {row.subject_id: row.due_reviews for row in due_reviews_agg}

    # 3) user levels per subject
    levels = (
        db.query(UserLevelModel)
        .filter(UserLevelModel.user_id == user_id)
        .filter(UserLevelModel.deleted == False)  # noqa
        .filter(UserLevelModel.subject_id.in_(subject_ids))
        .all()
    )
    level_map = {lv.subject_id: lv.level for lv in levels}

    out: list[SubjectProgressOut] = []
    for s in subjects:
        a = attempts_map.get(s.id)
        attempts_count = int(a.attempts_count) if a else 0
        correct_count = int(a.correct_count) if a and a.correct_count is not None else 0
        accuracy = (correct_count / attempts_count) if attempts_count > 0 else 0.0

        out.append(
            SubjectProgressOut(
                subject_id=s.id,
                subject_name=s.name,
                level=float(level_map.get(s.id, 5.0)),  # default 5.0 αν δεν υπάρχει
                attempts_count=attempts_count,
                accuracy=accuracy,
                due_reviews=int(due_map.get(s.id, 0)),
            )
        )

    return out


@router.get("/student/{user_id}/subject/{subject_id}/modules", response_model=list[ModuleProgressOut])
def student_modules_progress(user_id: int, subject_id: int, db: Session = Depends(get_db)):
    today = date.today()

    modules = (
        db.query(ModuleModel)
        .filter(ModuleModel.subject_id == subject_id)
        .filter(ModuleModel.deleted == False)  # noqa
        .all()
    )
    if not modules:
        return []

    module_ids = [m.id for m in modules]

    # questions_total per module
    q_total = (
        db.query(
            QuestionModel.module_id.label("module_id"),
            func.count(QuestionModel.id).label("questions_total"),
        )
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.module_id.in_(module_ids))
        .group_by(QuestionModel.module_id)
        .all()
    )
    q_total_map = {row.module_id: int(row.questions_total) for row in q_total}

    # attempted_questions DISTINCT + accuracy per module (attempts->questions)
    attempts_agg = (
        db.query(
            QuestionModel.module_id.label("module_id"),
            func.count(distinct(AttemptModel.question_id)).label("attempted_questions"),
            func.count(AttemptModel.id).label("attempts_count"),
            func.sum(case((AttemptModel.is_correct == True, 1), else_=0)).label("correct_count"),
        )
        .join(QuestionModel, QuestionModel.id == AttemptModel.question_id)
        .filter(AttemptModel.user_id == user_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.module_id.in_(module_ids))
        .group_by(QuestionModel.module_id)
        .all()
    )
    attempts_map = {row.module_id: row for row in attempts_agg}

    # due_reviews per module (card_meta->questions)
    due_reviews_agg = (
        db.query(
            QuestionModel.module_id.label("module_id"),
            func.count(CardMetaModel.id).label("due_reviews"),
        )
        .join(QuestionModel, QuestionModel.id == CardMetaModel.question_id)
        .filter(CardMetaModel.user_id == user_id)
        .filter(CardMetaModel.deleted == False)  # noqa
        .filter(CardMetaModel.next_review != None)  # noqa
        .filter(CardMetaModel.next_review <= today)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.module_id.in_(module_ids))
        .group_by(QuestionModel.module_id)
        .all()
    )
    due_map = {row.module_id: int(row.due_reviews) for row in due_reviews_agg}

    out: list[ModuleProgressOut] = []
    for m in modules:
        a = attempts_map.get(m.id)
        attempted_questions = int(a.attempted_questions) if a else 0
        attempts_count = int(a.attempts_count) if a else 0
        correct_count = int(a.correct_count) if a and a.correct_count is not None else 0
        accuracy = (correct_count / attempts_count) if attempts_count > 0 else 0.0

        out.append(
            ModuleProgressOut(
                module_id=m.id,
                module_title=m.title,
                questions_total=int(q_total_map.get(m.id, 0)),
                attempted_questions=attempted_questions,
                accuracy=accuracy,
                due_reviews=int(due_map.get(m.id, 0)),
            )
        )

    return out


@router.get("/student/{user_id}/review-summary", response_model=ReviewSummaryOut)
def review_summary(user_id: int, db: Session = Depends(get_db)):
    today = date.today()
    end = today + timedelta(days=6)

    base = (
        db.query(CardMetaModel)
        .filter(CardMetaModel.user_id == user_id)
        .filter(CardMetaModel.deleted == False)  # noqa
        .filter(CardMetaModel.next_review != None)  # noqa
    )

    due_today = base.filter(CardMetaModel.next_review == today).count()
    overdue = base.filter(CardMetaModel.next_review < today).count()

    # next 7 days counts grouped by date
    rows = (
        db.query(CardMetaModel.next_review, func.count(CardMetaModel.id))
        .filter(CardMetaModel.user_id == user_id)
        .filter(CardMetaModel.deleted == False)  # noqa
        .filter(CardMetaModel.next_review != None)  # noqa
        .filter(CardMetaModel.next_review >= today)
        .filter(CardMetaModel.next_review <= end)
        .group_by(CardMetaModel.next_review)
        .order_by(CardMetaModel.next_review.asc())
        .all()
    )
    count_map = {r[0]: int(r[1]) for r in rows}

    next_7_days = []
    for i in range(7):
        d = today + timedelta(days=i)
        next_7_days.append(ReviewDayCount(day=d, count=count_map.get(d, 0)))

    return ReviewSummaryOut(
        due_today=due_today,
        overdue=overdue,
        next_7_days=next_7_days,
    )


from app.schemas.reports import TeacherSubjectSummaryOut  # πρόσθεσε στο import group

@router.get("/teacher/subject/{subject_id}/summary", response_model=TeacherSubjectSummaryOut)
def teacher_subject_summary(subject_id: int, db: Session = Depends(get_db)):
    subject = (
        db.query(SubjectModel)
        .filter(SubjectModel.id == subject_id)
        .filter(SubjectModel.deleted == False)  # noqa
        .first()
    )
    if not subject:
        return TeacherSubjectSummaryOut(
            subject_id=subject_id,
            subject_name="(not found)",
            unique_students=0,
            attempts_count=0,
            accuracy=0.0,
            questions_total=0,
        )

    # total questions in subject
    questions_total = (
        db.query(func.count(QuestionModel.id))
        .filter(QuestionModel.subject_id == subject_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .scalar()
    ) or 0

    # attempts + correct across ALL students for that subject
    row = (
        db.query(
            func.count(AttemptModel.id).label("attempts_count"),
            func.sum(case((AttemptModel.is_correct == True, 1), else_=0)).label("correct_count"),
            func.count(distinct(AttemptModel.user_id)).label("unique_students"),
        )
        .join(QuestionModel, QuestionModel.id == AttemptModel.question_id)
        .filter(QuestionModel.subject_id == subject_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(QuestionModel.deleted == False)  # noqa
        .first()
    )

    attempts_count = int(row.attempts_count) if row and row.attempts_count is not None else 0
    correct_count = int(row.correct_count) if row and row.correct_count is not None else 0
    unique_students = int(row.unique_students) if row and row.unique_students is not None else 0
    accuracy = (correct_count / attempts_count) if attempts_count > 0 else 0.0

    return TeacherSubjectSummaryOut(
        subject_id=subject.id,
        subject_name=subject.name,
        unique_students=unique_students,
        attempts_count=attempts_count,
        accuracy=accuracy,
        questions_total=int(questions_total),
    )


from app.schemas.reports import TeacherModuleSummaryOut


@router.get(
    "/teacher/subject/{subject_id}/modules",
    response_model=list[TeacherModuleSummaryOut],
)
def teacher_subject_modules_summary(subject_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(
            ModuleModel.id.label("module_id"),
            ModuleModel.title.label("module_title"),
            func.count(AttemptModel.id).label("attempts_count"),
            func.sum(case((AttemptModel.is_correct == True, 1), else_=0)).label("correct_count"),
            func.count(distinct(AttemptModel.user_id)).label("unique_students"),
        )
        .join(QuestionModel, QuestionModel.module_id == ModuleModel.id)
        .join(AttemptModel, AttemptModel.question_id == QuestionModel.id)
        .filter(ModuleModel.subject_id == subject_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(AttemptModel.deleted == False)  # noqa
        .group_by(ModuleModel.id)
        .all()
    )

    out: list[TeacherModuleSummaryOut] = []

    for r in rows:
        attempts = int(r.attempts_count or 0)
        correct = int(r.correct_count or 0)
        accuracy = (correct / attempts) if attempts > 0 else 0.0

        out.append(
            TeacherModuleSummaryOut(
                module_id=r.module_id,
                module_title=r.module_title,
                attempts_count=attempts,
                accuracy=accuracy,
                unique_students=int(r.unique_students or 0),
            )
        )

    # ταξινόμηση από χειρότερο → καλύτερο
    out.sort(key=lambda x: x.accuracy)

    return out

@router.get("/teacher/subject/{subject_id}/timeline")
def teacher_subject_timeline(subject_id: int, days: int = 14, db: Session = Depends(get_db)):
    # last N days (including today)
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    rows = (
        db.query(
            func.date(AttemptModel.created_at).label("day"),
            func.count(AttemptModel.id).label("attempts"),
            func.sum(case((AttemptModel.is_correct == True, 1), else_=0)).label("correct"),
            func.count(distinct(AttemptModel.user_id)).label("unique_students"),
        )
        .join(QuestionModel, QuestionModel.id == AttemptModel.question_id)
        .filter(QuestionModel.subject_id == subject_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(AttemptModel.created_at >= start)
        .group_by(func.date(AttemptModel.created_at))
        .order_by(func.date(AttemptModel.created_at).asc())
        .all()
    )

    out = []
    for r in rows:
        attempts = int(r.attempts or 0)
        correct = int(r.correct or 0)
        acc = (correct / attempts) if attempts > 0 else 0.0
        out.append({
            "day": str(r.day),
            "attempts": attempts,
            "accuracy": acc,
            "unique_students": int(r.unique_students or 0),
        })

    return {"subject_id": subject_id, "days": out}

@router.get("/teacher/subject/{subject_id}/most-wrong")
def teacher_subject_most_wrong(subject_id: int, limit: int = 5, db: Session = Depends(get_db)):
    rows = (
        db.query(
            QuestionModel.id.label("question_id"),
            QuestionModel.prompt.label("prompt"),
            func.count(AttemptModel.id).label("attempts"),
            func.sum(case((AttemptModel.is_correct == False, 1), else_=0)).label("wrong"),
        )
        .join(AttemptModel, AttemptModel.question_id == QuestionModel.id)
        .filter(QuestionModel.subject_id == subject_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.status == "approved")
        .filter(AttemptModel.deleted == False)  # noqa
        .group_by(QuestionModel.id)
        .order_by(desc(func.sum(case((AttemptModel.is_correct == False, 1), else_=0))))
        .limit(limit)
        .all()
    )

    out = []
    for r in rows:
        attempts = int(r.attempts or 0)
        wrong = int(r.wrong or 0)
        out.append({
            "question_id": int(r.question_id),
            "prompt": r.prompt,
            "attempts": attempts,
            "wrong": wrong,
            "wrong_rate": (wrong / attempts) if attempts else 0.0,
        })
    return out

@router.get("/teacher/question/{question_id}/answer-distribution")
def teacher_question_answer_distribution(question_id: int, db: Session = Depends(get_db)):
    # total attempts for this question (with selected_index)
    total = (
        db.query(func.count(AttemptModel.id))
        .filter(AttemptModel.question_id == question_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(AttemptModel.selected_index != None)  # noqa
        .scalar()
    ) or 0

    rows = (
        db.query(
            AttemptModel.selected_index.label("selected_index"),
            func.count(AttemptModel.id).label("cnt"),
        )
        .filter(AttemptModel.question_id == question_id)
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(AttemptModel.selected_index != None)  # noqa
        .group_by(AttemptModel.selected_index)
        .order_by(AttemptModel.selected_index.asc())
        .all()
    )

    dist = []
    for r in rows:
        cnt = int(r.cnt or 0)
        dist.append({
            "selected_index": int(r.selected_index),
            "count": cnt,
            "pct": (cnt / total) if total else 0.0,
        })

    return {"question_id": question_id, "total": int(total), "distribution": dist}

@router.get("/teacher/subject/{subject_id}/answer-distribution")
def teacher_subject_answer_distribution(subject_id: int, db: Session = Depends(get_db)):
    # φέρνουμε όλες τις approved questions του subject
    qs = (
        db.query(QuestionModel.id, QuestionModel.prompt, QuestionModel.choices)
        .filter(QuestionModel.subject_id == subject_id)
        .filter(QuestionModel.deleted == False)  # noqa
        .filter(QuestionModel.status == "approved")
        .all()
    )

    if not qs:
        return []

    qids = [q.id for q in qs]

    # counts ανά (question_id, selected_index)
    rows = (
        db.query(
            AttemptModel.question_id.label("question_id"),
            AttemptModel.selected_index.label("selected_index"),
            func.count(AttemptModel.id).label("cnt"),
        )
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(AttemptModel.question_id.in_(qids))
        .filter(AttemptModel.selected_index != None)  # noqa
        .group_by(AttemptModel.question_id, AttemptModel.selected_index)
        .all()
    )

    # total ανά question_id
    totals = (
        db.query(
            AttemptModel.question_id.label("question_id"),
            func.count(AttemptModel.id).label("total"),
        )
        .filter(AttemptModel.deleted == False)  # noqa
        .filter(AttemptModel.question_id.in_(qids))
        .filter(AttemptModel.selected_index != None)  # noqa
        .group_by(AttemptModel.question_id)
        .all()
    )
    total_map = {t.question_id: int(t.total or 0) for t in totals}

    # counts map
    cnt_map = {}
    for r in rows:
        cnt_map.setdefault(int(r.question_id), {})[int(r.selected_index)] = int(r.cnt or 0)

    out = []
    for q in qs:
        choices = q.choices or []
        n_choices = len(choices)
        total = total_map.get(q.id, 0)

        # ✅ Θέλεις να εμφανίζει ΟΛΕΣ τις επιλογές με 0% αν δεν επιλέχθηκαν
        dist = []
        for i in range(n_choices):
            cnt = cnt_map.get(q.id, {}).get(i, 0)
            pct = (cnt / total) if total else 0.0
            dist.append({"selected_index": i, "count": cnt, "pct": pct})

        out.append({
            "question_id": int(q.id),
            "prompt": q.prompt,
            "total": int(total),
            "distribution": dist,
        })

    return out
