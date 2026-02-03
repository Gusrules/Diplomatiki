from pydantic import BaseModel
from typing import List

class FlashcardItem(BaseModel):
    front: str
    back: str

class FlashcardSetOut(BaseModel):
    resource_id: int
    module_id: int
    title: str
    flashcards: List[FlashcardItem]

    class Config:
        from_attributes = True
