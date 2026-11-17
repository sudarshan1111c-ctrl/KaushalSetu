# migrate.py – safe schema verification & migration for workforce_requests
# Run with: python migrate.py

"""This script ensures the SQLite database used by the Flask app
contains all required columns in the `workforce_requests` table.
It resolves the actual instance database path, prints the PRAGMA
information before and after any migration, and adds only missing
columns using a transaction (SQLAlchemy 2.x compatible).
"""

import sys
from pathlib import Path
from app import create_app, db
from sqlalchemy import text

app = create_app()


def get_absolute_db_path(engine) -> Path:
    """Return the absolute Path to the SQLite file used by the engine.
    For a relative path (e.g., "kaushalsetu.db") we resolve it
    against Flask's instance_path, which is where the file actually lives.
    """
    raw_path = engine.url.database
    if not raw_path:
        raise RuntimeError("Engine does not have a SQLite database path.")
    p = Path(raw_path)
    if not p.is_absolute():
        # Resolve relative to the Flask instance folder
        p = (Path(app.instance_path) / p).resolve()
    else:
        p = p.resolve()
    return p


def pragma_columns(engine):
    """Execute PRAGMA table_info and return a list of column names.
    Also prints each row for full visibility.
    """
    with engine.connect() as conn:
        print("\n--- PRAGMA table_info('workforce_requests') ---")
        result = conn.execute(text("PRAGMA table_info('workforce_requests')"))
        rows = result.fetchall()
        for row in rows:
            print("PRAGMA row:", dict(row._mapping))
        return [row._mapping["name"] for row in rows]


def main():
    with app.app_context():
        engine = db.engine
        # 1️⃣ Resolve and print absolute DB path
        db_path = get_absolute_db_path(engine)
        print("Using SQLite database file:", db_path)
        if not db_path.is_file():
            print("ERROR: Database file does not exist at the resolved path.")
            sys.exit(1)

        # 2️⃣ Show current schema via PRAGMA (definitive view)
        before_cols = pragma_columns(engine)
        print("\nCurrent columns (before migration):", before_cols)

        # 3️⃣ Define required columns (name -> SQLite type). 'id' and 'order_id' are already present.
        required = {
            "job_title": "TEXT",
            "required_skills": "TEXT",
            "needed_quantity": "INTEGER",
            "location": "TEXT",
            "payment_amount": "REAL",
            "duration_days": "INTEGER",
            "description": "TEXT",
            "status": "TEXT",
        }
        missing = [col for col in required if col not in before_cols]
        if not missing:
            print("\nAll required columns already exist – no migration needed.")
        else:
            print("\nMissing columns to be added:", missing)
            for col in missing:
                col_type = required[col]
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE workforce_requests ADD COLUMN {col} {col_type}"))
                    print(f"Added column {col} ({col_type})")
                except Exception as e:
                    print(f"FAILED to add column {col}: {e}")
                    sys.exit(1)

        # 4️⃣ Re‑fetch schema after any ALTER statements
        after_cols = pragma_columns(engine)
        print("\nColumns after migration attempt:", after_cols)

        # 5️⃣ Final verification – ensure every required column (including id & order_id) is present
        # Retrieve full list again for safety
        final_cols = after_cols
        required_with_keys = ["id", "order_id"] + list(required.keys())
        still_missing = [col for col in required_with_keys if col not in final_cols]
        if still_missing:
            print("\nERROR: The following required columns are still missing after migration:", still_missing)
            sys.exit(1)
        else:
            print("\nVerification successful: all required columns are present.")

if __name__ == "__main__":
    main()
