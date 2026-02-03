import os
from pathlib import Path
from dotenv import load_dotenv
import sqlite3

HERE = Path(__file__).resolve().parent
ENV_PATH = HERE / ".env"

def resolve_sqlite_path(database_url: str) -> Path:
    # supports:
    # sqlite:///./app.db
    # sqlite:////C:/path/app.db
    if not database_url.startswith("sqlite"):
        raise RuntimeError("This migration script supports only sqlite DATABASE_URL")

    raw = database_url.replace("sqlite:///", "", 1)

    # absolute windows path form sqlite:////C:/...
    if raw.startswith("/"):
        # "/C:/x/y.db" -> "C:/x/y.db"
        raw = raw.lstrip("/")
        return Path(raw)

    # relative path (./app.db) relative to backend/app
    return (HERE / raw).resolve()

def column_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]  # r[1] = name
    return col in cols

def add_column(cur, table: str, ddl: str):
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

def main():
    if not ENV_PATH.exists():
        raise RuntimeError(f".env not found at {ENV_PATH}")

    load_dotenv(dotenv_path=ENV_PATH)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL missing in backend/app/.env")

    db_path = resolve_sqlite_path(db_url)

    if not db_path.exists():
        raise RuntimeError(f"SQLite file not found: {db_path}\nCheck DATABASE_URL in backend/app/.env")

    print("Using SQLite DB:", db_path)

    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    # make sure table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
    if not cur.fetchone():
        raise RuntimeError("Table 'questions' not found. Run backend once so create_all() creates tables.")

    # Add columns if missing
    if not column_exists(cur, "questions", "status"):
        print("Adding column: status")
        add_column(cur, "questions", "status VARCHAR(20) NOT NULL DEFAULT 'pending'")

    if not column_exists(cur, "questions", "reviewed_by"):
        print("Adding column: reviewed_by")
        add_column(cur, "questions", "reviewed_by INTEGER")

    if not column_exists(cur, "questions", "reviewed_at"):
        print("Adding column: reviewed_at")
        add_column(cur, "questions", "reviewed_at DATETIME")

    if not column_exists(cur, "questions", "updated_at"):
        print("Adding column: updated_at")
        add_column(cur, "questions", "updated_at DATETIME")

    con.commit()
    con.close()
    print("OK ✅ Migration completed.")

if __name__ == "__main__":
    main()
