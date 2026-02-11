# src/scripts/migrate_card_meta_sqlite.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "app.db"

COLUMNS_TO_ADD = [
    ("easiness_factor", "FLOAT", "2.5"),
    ("interval_days", "INTEGER", "0"),
    ("next_review_at", "DATETIME", None),
    ("last_reviewed_at", "DATETIME", None),
    ("correct_streak", "INTEGER", "0"),
    ("incorrect_streak", "INTEGER", "0"),
    ("status", "TEXT", "'new'"),
]

def column_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

def main():
    print("Starting migration...")
    print(f"Database: {DB_PATH}")

    if not DB_PATH.exists():
        raise SystemExit(f"DB not found at: {DB_PATH}")

    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()

    # Add missing columns
    for col, coltype, default in COLUMNS_TO_ADD:
        if column_exists(cur, "card_meta", col):
            print(f"  ✓ {col} (already exists)")
            continue

        if default is None:
            sql = f"ALTER TABLE card_meta ADD COLUMN {col} {coltype}"
        else:
            sql = f"ALTER TABLE card_meta ADD COLUMN {col} {coltype} DEFAULT {default}"

        print(f"  + {col} (added)")
        cur.execute(sql)

    # Ensure unique index
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_card_meta_user_question
        ON card_meta(user_id, question_id)
    """)

    con.commit()
    con.close()
    print("Done.")

if __name__ == "__main__":
    main()
