from pydantic import BaseModel
from typing import List, Optional


class WeakModuleOut(BaseModel):
    module_id: int
    module_title: str
    accuracy: float


class RecommendedResourceOut(BaseModel):
    resource_id: int
    title: str
    type: str


class QuizRecommendationOut(BaseModel):
    subject_id: int
    module_id: Optional[int]
    suggested_questions: int


class RecommendationsOut(BaseModel):
    user_id: int
    subject_id: int
    weak_modules: List[WeakModuleOut]
    recommended_resources: List[RecommendedResourceOut]
    quiz_recommendation: Optional[QuizRecommendationOut]
