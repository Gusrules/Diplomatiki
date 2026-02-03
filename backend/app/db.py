from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path
import os

# Base σε ξεχωριστό αρχείο (σωστό)
from app.db_base import Base

# --- Load .env from the SAME directory as this file ---
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
print(">>> DATABASE_URL =", DATABASE_URL)
print(">>> CWD =", os.getcwd())
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing! Check your .env file location.")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
