from pydantic import BaseModel
from typing import Literal


ResourceType = Literal["study_guide", "flashcard", "explanation"]
FileType = Literal["pdf", "docx", "txt", "json"]


class ResourceBase(BaseModel):
    module_id: int
    type: ResourceType
    title: str
    file_path: str
    file_type: FileType
    uploaded_by: int | None = None


class ResourceCreate(ResourceBase):
    content: str | None = None   # ✅ επιτρέπουμε να στείλεις κείμενο ύλης


class ResourceOut(ResourceBase):
    id: int

    class Config:
        from_attributes = True


class ResourceOutDetail(ResourceOut):
    content: str | None = None   # ✅ για GET/{id} και για debugging/AI


class ResourceContentUpdate(BaseModel):
    content: str
