"""
Build the University Training Database from scratch.

Usage:
    python scripts/build_university_db.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow running as `python scripts/build_university_db.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_layer import connect, count_rows, execute_sql_file
from src.logging_setup import setup_logging

DB_FILE = PROJECT_ROOT / "data" / "raw" / "university.db"
SCHEMA_FILE = PROJECT_ROOT / "database" / "schema.sql"
SEED_FILE = PROJECT_ROOT / "database" / "seed_data.sql"

logger = logging.getLogger(__name__)


def main() -> int:
    setup_logging()
    logger.info("=" * 60)
    logger.info("Building University Training Database")
    logger.info("=" * 60)

    # Fresh build
    if DB_FILE.exists():
        DB_FILE.unlink()
        logger.info("Removed existing database: %s", DB_FILE)

    with connect(DB_FILE) as conn:
        execute_sql_file(conn, SCHEMA_FILE)
        execute_sql_file(conn, SEED_FILE)

        print("\n" + "=" * 60)
        print("University Training Database — Summary")
        print("=" * 60)
        for table in ("instructors", "students", "courses", "enrollments", "assessments"):
            n = count_rows(conn, table)
            print(f"  {table:15s} : {n:3d} rows")
        print("=" * 60)
        print(f"Database file: {DB_FILE}")
        print("=" * 60)

    logger.info("Database built successfully: %s", DB_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
