from fastapi import FastAPI
from app.db import engine
from app.db_base import Base

from app.routers import student as student_router
from app.routers import teacher as teacher_router
from app.routers import subject as subject_router
from app.routers import module as module_router
from app.routers import question as question_router
from app.routers import quiz as quiz_router
from app.routers import attempt as attempt_router
from app.routers import adaptive_quiz as adaptive_quiz_router
from app.routers import review as review_router
from app.routers import resource as resource_router
from app.routers import ai as ai_router
from app.routers import reports as reports_router
from app.routers import flashcard as flashcard_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers import enrollment as enrollment_router
from app.routers import auth as auth_router
from app.routers import dev_seed as dev_seed_router
from app.routers import dev_reset_passwords as dev_reset_passwords_router



app = FastAPI(openapi_url="/openapi.json", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(student_router.router)
app.include_router(teacher_router.router)
app.include_router(subject_router.router)
app.include_router(module_router.router)
app.include_router(question_router.router)
app.include_router(quiz_router.router)
app.include_router(attempt_router.router)
app.include_router(adaptive_quiz_router.router)
app.include_router(review_router.router)
app.include_router(resource_router.router)
app.include_router(ai_router.router)
app.include_router(reports_router.router)
app.include_router(flashcard_router.router)
app.include_router(enrollment_router.router)
app.include_router(auth_router.router)
app.include_router(dev_seed_router.router)
app.include_router(dev_reset_passwords_router.router)

@app.get("/")
def home():
    return {"message": "API is running!"}
