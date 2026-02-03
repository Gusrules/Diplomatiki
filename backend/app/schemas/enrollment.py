from pydantic import BaseModel, ConfigDict
from datetime import datetime

class EnrollmentCreate(BaseModel):
    user_id: int
    subject_id: int

class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    subject_id: int
    created_at: datetime
