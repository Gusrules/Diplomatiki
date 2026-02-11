import sqlite3
from pathlib import Path

# Get the database path
backend_dir = Path(__file__).resolve().parent
db_path = backend_dir / "app.db"

print(f"Fixing database at: {db_path}")

# Connect to the database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Tables to check (those with deleted_at column)
tables_with_deleted_at = [
    'modules', 'subjects', 'questions', 'quizzes', 'resources',
    'teachers', 'students', 'subject_teachers', 'attempts',
    'card_metas', 'user_levels'
]

for table in tables_with_deleted_at:
    try:
        # Update all empty strings in deleted_at to NULL
        cursor.execute(f"UPDATE {table} SET deleted_at = NULL WHERE deleted_at = ''")
        
        # Verify the fix
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE deleted_at = ''")
        remaining = cursor.fetchone()[0]
        
        if remaining > 0:
            print(f"⚠️  {table}: {remaining} empty strings remaining")
        else:
            print(f"✓ {table}: Fixed (no empty strings)")
    except Exception as e:
        print(f"- {table}: Skipped ({str(e)[:50]})")

conn.commit()
conn.close()

print("\n✓ Database fix completed!")


