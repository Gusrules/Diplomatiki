from pydantic import BaseModel
from datetime import datetime

class ModuleBase(BaseModel):
    subject_id: int
    title: str
    description: str | None = None

class ModuleCreate(ModuleBase):
    pass

class ModuleOut(ModuleBase):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True
