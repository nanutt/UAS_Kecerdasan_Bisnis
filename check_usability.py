import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MART_DB_FILE = PROJECT_ROOT / "Data" / "04_data_mart" / "mart_health_summary.db"

print(f"Checking database: {MART_DB_FILE}")

if not MART_DB_FILE.exists():
    print("❌ Database file not found!")
    exit(1)

with sqlite3.connect(MART_DB_FILE) as conn:
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mart_usability_score'")
    if not cursor.fetchone():
        print("❌ mart_usability_score table does not exist!")
        exit(1)

    # Check data
    cursor.execute("SELECT COUNT(*) FROM mart_usability_score")
    count = cursor.fetchone()[0]
    print(f"Total records in mart_usability_score: {count}")

    if count > 0:
        cursor.execute("SELECT * FROM mart_usability_score ORDER BY date DESC LIMIT 5")
        print("\nLatest usability scores:")
        for row in cursor.fetchall():
            print(f"Date: {row[0]}, Completion: {row[1]}%, Time: {row[2]}s, Error: {row[3]}%, Score: {row[4]}")
    else:
        print("No data in mart_usability_score table")
