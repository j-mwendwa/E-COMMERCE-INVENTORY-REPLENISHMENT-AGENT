"""Seed the PostgreSQL database with mock inventory data.

Usage:
    python scripts/seed_db.py
    python scripts/seed_db.py postgresql://user:pass@localhost:5432/inventory
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    import psycopg2
    from src.config import settings
    from src.db.schema import SCHEMA_SQL, SEED_SQL

    url = sys.argv[1] if len(sys.argv) > 1 else settings.database_url
    if not url:
        print("No DATABASE_URL. Pass a connection string or set DATABASE_URL in .env")
        sys.exit(1)

    conn = psycopg2.connect(url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            print("Schema created.")
            cur.execute(SEED_SQL)
            print("Seed data inserted.")
    finally:
        conn.close()

    print("Database seeded successfully.")


if __name__ == "__main__":
    main()
