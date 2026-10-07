"""
Star Schema Builder — OLAP Layer
==================================

Converts 3NF OLTP data (university.db) into a Star Schema of
fact + dimension tables, stored as Parquet (Gold layer).

Design (Ch 7 of the Data Engineering Guide):
    Facts (2):
        fact_student_performance  — grain = 1 assessment
        fact_enrollment           — grain = 1 enrollment (factless)

    Dimensions (4):
        dim_students              — 1 row = 1 student
        dim_courses               — 1 row = 1 course
        dim_instructors           — 1 row = 1 instructor
        dim_time                  — 1 row = 1 calendar date

Why Star Schema?
    - Faster analytical queries (fewer JOINs)
    - Denormalized dimensions = single-scan reads
    - Clear grain for safe aggregation
    - Native to OLAP engines (Snowflake, BigQuery, DuckDB)

Source:  data/raw/university.db
Output:  data/gold/*.parquet
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.warehouse.parquet_writer import write_parquet

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DB: Path = Path("data/raw/university.db")
DEFAULT_OUTPUT: Path = Path("data/gold")

EXPECTED_TABLES: set[str] = {
    "students", "instructors", "courses", "enrollments", "assessments",
}


# ---------------------------------------------------------------------------
# Star Schema Builder
# ---------------------------------------------------------------------------

class StarSchemaBuilder:
    """Builds a Star Schema (2 facts + 4 dims) from a 3NF OLTP database."""

    def __init__(
        self,
        db_path: Path = DEFAULT_DB,
        output_dir: Path = DEFAULT_OUTPUT,
    ) -> None:
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    # -- Public API ---------------------------------------------------------

    def build_all(self) -> dict[str, Path]:
        """Build every fact + dimension and write to Parquet.

        Returns:
            Mapping: {table_name: parquet_path}
        """
        logger.info("=" * 60)
        logger.info("STAR SCHEMA BUILDER")
        logger.info("=" * 60)

        self._check_schema()

        # 1. Extract from OLTP (3NF)
        students_df = self._read_table("students")
        courses_df = self._read_table("courses")
        instructors_df = self._read_table("instructors")
        enrollments_df = self._read_table("enrollments")
        assessments_df = self._read_table("assessments")

        # 2. Build dimensions
        dim_students = self._build_dim_students(students_df)
        dim_courses = self._build_dim_courses(courses_df)
        dim_instructors = self._build_dim_instructors(instructors_df)
        dim_time = self._build_dim_time(enrollments_df)

        # 3. Build facts
        fact_student_performance = self._build_fact_student_performance(
            assessments_df, enrollments_df, courses_df
        )
        fact_enrollment = self._build_fact_enrollment(enrollments_df)

        # 4. Write everything to Parquet
        outputs: dict[str, Path] = {}
        outputs["dim_students"] = write_parquet(dim_students, self.output_dir / "dim_students.parquet")
        outputs["dim_courses"] = write_parquet(dim_courses, self.output_dir / "dim_courses.parquet")
        outputs["dim_instructors"] = write_parquet(dim_instructors, self.output_dir / "dim_instructors.parquet")
        outputs["dim_time"] = write_parquet(dim_time, self.output_dir / "dim_time.parquet")
        outputs["fact_student_performance"] = write_parquet(fact_student_performance, self.output_dir / "fact_student_performance.parquet")
        outputs["fact_enrollment"] = write_parquet(fact_enrollment, self.output_dir / "fact_enrollment.parquet")

        logger.info("Star Schema built: %d tables", len(outputs))
        return outputs

    # -- Extraction --------------------------------------------------------

    def _check_schema(self) -> None:
        """Verify the DB contains all expected tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            actual = {row[0] for row in cursor.fetchall()}

        missing = EXPECTED_TABLES - actual
        if missing:
            raise ValueError(
                f"Missing tables in {self.db_path}: {sorted(missing)}. "
                f"Found: {sorted(actual)}"
            )
        logger.info("Schema check passed: 5/5 tables found.")

    def _read_table(self, table: str) -> pd.DataFrame:
        """Read an entire table from SQLite into a DataFrame."""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        logger.info("Extracted %-15s %d rows x %d cols", table, len(df), len(df.columns))
        return df

    # -- Dimensions ---------------------------------------------------------

    @staticmethod
    def _select_existing(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Return only the columns that exist in df (schema-resilient)."""
        return df[[c for c in cols if c in df.columns]].copy()

    @staticmethod
    def _to_int64(series: pd.Series) -> pd.Series:
        return pd.to_numeric(series, errors="coerce").astype("Int64")

    def _build_dim_students(self, students_df: pd.DataFrame) -> pd.DataFrame:
        """Grain: 1 row = 1 student."""
        dim = self._select_existing(
            students_df,
            ["student_id", "full_name", "gender", "date_of_birth", "city"],
        )
        if "student_id" in dim.columns:
            dim["student_id"] = self._to_int64(dim["student_id"])
        return dim

    def _build_dim_courses(self, courses_df: pd.DataFrame) -> pd.DataFrame:
        """Grain: 1 row = 1 course."""
        dim = self._select_existing(
            courses_df,
            ["course_id", "course_name", "credit_hours", "instructor_id"],
        )
        for col in ("course_id", "instructor_id", "credit_hours"):
            if col in dim.columns:
                dim[col] = self._to_int64(dim[col])
        return dim

    def _build_dim_instructors(self, instructors_df: pd.DataFrame) -> pd.DataFrame:
        """Grain: 1 row = 1 instructor."""
        dim = self._select_existing(
            instructors_df,
            ["instructor_id", "full_name", "department", "email"],
        )
        if "instructor_id" in dim.columns:
            dim["instructor_id"] = self._to_int64(dim["instructor_id"])
        return dim

    def _build_dim_time(self, enrollments_df: pd.DataFrame) -> pd.DataFrame:
        """Grain: 1 row = 1 calendar date (from min to max in enrollments)."""
        if "enrollment_date" not in enrollments_df.columns:
            raise ValueError("enrollments table has no enrollment_date column.")

        dates = pd.to_datetime(enrollments_df["enrollment_date"], errors="coerce").dropna()
        if dates.empty:
            raise ValueError("No valid enrollment_date values found.")

        date_range = pd.date_range(
            start=dates.min().date(),
            end=dates.max().date(),
            freq="D",
        )

        return pd.DataFrame({
            "time_id": [int(d.strftime("%Y%m%d")) for d in date_range],
            "full_date": [d.date() for d in date_range],
            "year": [d.year for d in date_range],
            "month": [d.month for d in date_range],
            "day": [d.day for d in date_range],
            "weekday": [d.strftime("%A") for d in date_range],
            "is_weekend": [d.weekday() >= 5 for d in date_range],
        })

    # -- Facts -------------------------------------------------------------

    def _build_fact_student_performance(
        self,
        assessments_df: pd.DataFrame,
        enrollments_df: pd.DataFrame,
        courses_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Grain: 1 row = 1 assessment.

        Handles two possible schemas:
            - v2.0.0+ : assessments has `enrollment_id` (strong FK design)
            - v1.0.0  : assessments has `student_id` + `course_id` (weak design)
        """
        # Detect schema
        enrollment_cols = enrollments_df.columns.tolist()
        if "enrollment_id" in assessments_df.columns:
            join_cols = ["enrollment_id"]
        elif {"student_id", "course_id"}.issubset(assessments_df.columns):
            join_cols = ["student_id", "course_id"]
        else:
            raise ValueError(
                "Cannot link assessments to enrollments: missing "
                "enrollment_id or (student_id, course_id)."
            )

        # Attach enrollment keys
        df = assessments_df.merge(
            enrollments_df[["enrollment_id", "student_id", "course_id"]],
            on=join_cols,
            how="left",
        )

        # Attach instructor_id via courses
        df = df.merge(
            courses_df[["course_id", "instructor_id"]],
            on="course_id",
            how="left",
        )

        # Select final columns
        fact = self._select_existing(
            df,
            ["assessment_id", "enrollment_id", "student_id",
             "course_id", "instructor_id", "assessment_type", "score"],
        )

        # Cast types
        for col in ("assessment_id", "enrollment_id", "student_id",
                    "course_id", "instructor_id"):
            if col in fact.columns:
                fact[col] = self._to_int64(fact[col])

        if "score" in fact.columns:
            fact["score"] = pd.to_numeric(fact["score"], errors="coerce").astype("float64")

        return fact

    def _build_fact_enrollment(self, enrollments_df: pd.DataFrame) -> pd.DataFrame:
        """Grain: 1 row = 1 enrollment. Factless fact table (no measures)."""
        df = enrollments_df.copy()

        # Derive time_id from enrollment_date
        if "enrollment_date" in df.columns:
            dates = pd.to_datetime(df["enrollment_date"], errors="coerce")
            df["time_id"] = dates.dt.strftime("%Y%m%d")
            df["time_id"] = pd.to_numeric(df["time_id"], errors="coerce").astype("Int64")

        fact = self._select_existing(
            df,
            ["enrollment_id", "student_id", "course_id",
             "time_id", "semester"],
        )

        for col in ("enrollment_id", "student_id", "course_id", "time_id"):
            if col in fact.columns:
                fact[col] = self._to_int64(fact[col])

        return fact


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    builder = StarSchemaBuilder()
    outputs = builder.build_all()

    print()
    print("=" * 70)
    print("STAR SCHEMA OUTPUTS")
    print("=" * 70)
    for name, path in outputs.items():
        size_kb = path.stat().st_size / 1024
        print(f"  {name:<30} {size_kb:>8.2f} KB   {path.name}")
    print("=" * 70)