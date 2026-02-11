from pydantic import BaseModel
from typing import Optional, List


class NotificationItem(BaseModel):
    key: str                 # stable identifier (e.g. "due_reviews", "new_material")
    title: str
    message: str
    severity: str            # "info" | "warning"
    count: int = 0
    subject_id: Optional[int] = None
    subject_title: Optional[str] = None


class NotificationsOut(BaseModel):
    user_id: int
    items: List[NotificationItem]


class NotificationsSummaryOut(BaseModel):
    user_id: int
    total: int
    due_reviews: int
    new_material: int
