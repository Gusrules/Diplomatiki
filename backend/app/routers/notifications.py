from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.card_meta import CardMeta
from app.models.user_level import UserLevel
from app.models.subject import Subject

# Προσοχή: το μοντέλο resources μπορεί να λέγεται αλλιώς στο project σου.
# Αν το δικό σου είναι Resource ή StudyResource, άλλαξε μόνο αυτό import.
from app.models.resource import Resource  # <-- αν σκάσει ImportError, πες μου το όνομα του model

from app.schemas.notifications import (
    NotificationsOut,
    NotificationItem,
    NotificationsSummaryOut,
)
from app.models.module import Module

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsOut)
def get_notifications(
    user_id: int,
    days_new_material: int = 7,
    db: Session = Depends(get_db),
):
    items: list[NotificationItem] = []

    # 1) Due reviews (next_review <= today)
    today = date.today()
    due_count = (
        db.query(func.count(CardMeta.id))
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .filter(CardMeta.next_review <= today)
        .scalar()
    ) or 0

    if due_count > 0:
        items.append(
            NotificationItem(
                key="due_reviews",
                title="Επαναλήψεις διαθέσιμες",
                message="Έχεις προγραμματισμένη επανάληψη.",
                severity="warning",
                count=int(due_count),
            )
        )

    # 2) New material (resources) για subjects που “έχει” ο χρήστης (μέσω user_levels)
    # (χωρίς enrollment table)
    since = datetime.now(timezone.utc) - timedelta(days=days_new_material)

    subject_rows = (
        db.query(UserLevel.subject_id)
        .filter(UserLevel.user_id == user_id)
        .filter(UserLevel.deleted == False)  # noqa
        .all()
    )
    subject_ids = [sid for (sid,) in subject_rows]

    new_material_total = 0

    if subject_ids:
        # grouping ανά subject
        results = (
            db.query(
                Subject.id.label("subject_id"),
                func.count(Resource.id).label("cnt"),
            )
            .join(Module, Resource.module_id == Module.id)
            .join(Subject, Module.subject_id == Subject.id)
            .filter(Resource.deleted == False)  # noqa
            .filter(Subject.id.in_(subject_ids))
            .filter(Resource.created_at != None)  # noqa
            .filter(Resource.created_at >= since)
            .group_by(Subject.id)
            .all()
        )

        if results:
            # map subject titles
            subs = db.query(Subject).filter(Subject.id.in_([r[0] for r in results])).all()
            title_map = {s.id: getattr(s, "title", None) or getattr(s, "name", None) or f"Subject {s.id}" for s in subs}

            for subject_id, cnt in results:
                cnt = int(cnt or 0)
                if cnt <= 0:
                    continue
                new_material_total += cnt
                items.append(
                    NotificationItem(
                        key="new_material",
                        title="Νέο υλικό",
                        message="Υπάρχει νέο υλικό μελέτης διαθέσιμο.",
                        severity="info",
                        count=cnt,
                        subject_id=subject_id,
                        subject_title=title_map.get(subject_id),
                    )
                )

    return NotificationsOut(user_id=user_id, items=items)


@router.get("/summary", response_model=NotificationsSummaryOut)
def get_notifications_summary(
    user_id: int,
    days_new_material: int = 7,
    db: Session = Depends(get_db),
):
    today = date.today()

    due_reviews = (
        db.query(func.count(CardMeta.id))
        .filter(CardMeta.user_id == user_id)
        .filter(CardMeta.deleted == False)  # noqa
        .filter(CardMeta.next_review != None)  # noqa
        .filter(CardMeta.next_review <= today)
        .scalar()
    ) or 0

    subject_rows = (
        db.query(UserLevel.subject_id)
        .filter(UserLevel.user_id == user_id)
        .filter(UserLevel.deleted == False)  # noqa
        .all()
    )
    subject_ids = [sid for (sid,) in subject_rows]

    new_material = 0
    if subject_ids:
        since = datetime.now(timezone.utc) - timedelta(days=days_new_material)
        new_material = (
            db.query(func.count(Resource.id))
            .join(Module, Resource.module_id == Module.id)
            .join(Subject, Module.subject_id == Subject.id)
            .filter(Resource.deleted == False)  # noqa
            .filter(Subject.id.in_(subject_ids))
            .filter(Resource.created_at != None)  # noqa
            .filter(Resource.created_at >= since)
            .scalar()
        ) or 0


    total = int(due_reviews) + int(new_material)

    return NotificationsSummaryOut(
        user_id=user_id,
        total=total,
        due_reviews=int(due_reviews),
        new_material=int(new_material),
    )
