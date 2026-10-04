"""
Export student performance data from the University DB to CSV.

Pipeline:
    University DB → SQL → DataFrame → Validation → CSV

Usage:
    python scripts/export_student_report.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_layer import connect
from src.logging_setup import setup_logging
from src.query_layer import load_ml_features

DB_FILE = PROJECT_ROOT / "data" / "raw" / "university.db"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "student_performance.csv"

logger = logging.getLogger(__name__)


def validate_features(df) -> None:
    """Validate the ML feature table before saving."""
    required = {
        "student_id", "student_name", "city",
        "courses_count", "assessments_count",
        "average_score", "highest_score", "lowest_score",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("Feature table is empty.")

    valid_scores = df["average_score"].dropna()
    if not valid_scores.between(0, 100).all():
        raise ValueError("Invalid average_score values.")

    logger.info("Feature validation passed (%d rows).", len(df))


def main() -> int:
    setup_logging()
    logger.info("=" * 60)
    logger.info("Export Student Performance Report")
    logger.info("=" * 60)

    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    with connect(DB_FILE) as conn:
        df = load_ml_features(conn)

    validate_features(df)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    logger.info("Exported %d rows → %s", len(df), OUTPUT_CSV)

    print("\n" + "=" * 60)
    print("Student Performance — Exported")
    print("=" * 60)
    print(df.to_string(index=False))
    print("=" * 60)
    print(f"Output: {OUTPUT_CSV}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
