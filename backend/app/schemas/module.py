from pydantic import BaseModel

class ModuleBase(BaseModel):
    subject_id: int
    title: str
    description: str | None = None

class ModuleCreate(ModuleBase):
    pass

class ModuleOut(ModuleBase):
    id: int

    class Config:
        from_attributes = True
