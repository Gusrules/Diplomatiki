from pydantic import BaseModel
from typing import Literal


class AIGenerateQuestionsIn(BaseModel):
    subject_id: int
    module_id: int | None = None
    n: int = 3

class AIGenerateFromResourceIn(BaseModel):
    resource_id: int
    n: int = 5
    auto_add_to_quiz: bool = True
    quiz_id: int | None = None


class AIGenerateFromResourceOut(BaseModel):
    resource_id: int
    created: list[dict]
    count: int
    quiz_id: int | None = None

class AIGenerateFlashcardsIn(BaseModel):
    resource_id: int
    n: int = 8

class AIGenerateFlashcardsOut(BaseModel):
    source_resource_id: int
    flashcard_resource_id: int
    count: int