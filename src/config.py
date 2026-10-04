"""
Centralized configuration — Single Source of Truth.
All constants live here; no magic values elsewhere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# ─────────────────────────────────────────────────────────
# Project Paths
# ─────────────────────────────────────────────────────────
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
RAW_DIR: Final[Path] = DATA_DIR / "raw"
PROCESSED_DIR: Final[Path] = DATA_DIR / "processed"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"

RAW_FILE: Final[Path] = RAW_DIR / "students_raw.csv"
OUTPUT_FILE: Final[Path] = PROCESSED_DIR / "students_ml_ready.csv"
LOG_FILE: Final[Path] = LOGS_DIR / "pipeline.log"
DB_FILE: Final[Path] = DATA_DIR / "student_data.db"

# ─────────────────────────────────────────────────────────
# Schema Rules
# ─────────────────────────────────────────────────────────
REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"student_id", "name", "age", "gpa", "attendance", "city"}
)

NUMERIC_COLUMNS: Final[tuple[str, ...]] = (
    "student_id", "age", "gpa", "attendance",
)

TARGET_DTYPES: Final[dict[str, str]] = {
    "student_id": "Int64",
    "age": "Int64",
    "gpa": "float64",
    "attendance": "float64",
}

# ─────────────────────────────────────────────────────────
# Quality Rules
# ─────────────────────────────────────────────────────────
REQUIRED_NON_NULL: Final[tuple[str, ...]] = ("student_id", "name")
UNIQUE_COLUMNS: Final[tuple[str, ...]] = ("student_id",)

OUTLIER_RANGES: Final[dict[str, tuple[float, float]]] = {
    "age": (16, 80),
    "gpa": (0, 4),
    "attendance": (0, 100),
}

TEXT_FIELDS_TO_STRIP: Final[tuple[str, ...]] = ("name", "city")
TEXT_FIELDS_TO_TITLE: Final[tuple[str, ...]] = ("city",)
FILL_WITH_MEDIAN: Final[tuple[str, ...]] = ("age", "gpa", "attendance")

# ─────────────────────────────────────────────────────────
# Missing-Value Policy (documented)
# ─────────────────────────────────────────────────────────
MISSING_POLICY: Final[dict[str, str]] = {
    "name": "drop",
    "city": "fill_unknown",
    "age": "median",
    "gpa": "median",
    "attendance": "median",
}

# ─────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────
SEPARATOR_WIDTH: Final[int] = 60
SEPARATOR: Final[str] = "=" * SEPARATOR_WIDTH

LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024
LOG_BACKUP_COUNT: Final[int] = 5
LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | "
    "%(name)s | %(funcName)s:%(lineno)d | %(message)s"
)

DEFAULT_ENCODING: Final[str] = "utf-8"
DEFAULT_CHUNK_SIZE: Final[int] = 10_000

# ─────────────────────────────────────────────────────────
# Exit Codes
# ─────────────────────────────────────────────────────────
EXIT_SUCCESS: Final[int] = 0
EXIT_UNEXPECTED: Final[int] = 1
EXIT_FILE_NOT_FOUND: Final[int] = 2
EXIT_VALIDATION_ERROR: Final[int] = 3
EXIT_INTERRUPTED: Final[int] = 130
