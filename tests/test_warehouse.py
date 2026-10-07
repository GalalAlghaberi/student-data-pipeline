"""
Tests for src/warehouse/ — OLAP + Parquet Layer
=================================================

Coverage:
    - parquet_writer: write, read, compare, info
    - StarSchemaBuilder: dims, facts, end-to-end

Strategy:
    - Uses tmp_path for full isolation.
    - Builds a minimal SQLite fixture (mock_db) instead of relying on
      data/raw/university.db being present.
    - One integration test uses the real university.db if it exists.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.warehouse.parquet_writer import (
    compare_csv_vs_parquet,
    get_parquet_info,
    read_parquet,
    write_parquet,
)
from src.warehouse.star_schema import StarSchemaBuilder


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Small DataFrame used for parquet_writer tests."""
    return pd.DataFrame({
        "student_id": pd.array([1001, 1002, 1003], dtype="Int64"),
        "name": ["Ahmed", "Sara", "Khaled"],
        "age": pd.array([22, 21, 23], dtype="Int64"),
        "gpa": [3.5, 3.8, 3.1],
        "attendance": [92.0, 96.0, 88.0],
        "city": ["Sanaa", "Dhamar", "Ibb"],
    })


@pytest.fixture
def mock_db(tmp_path: Path) -> Path:
    """Create a minimal SQLite database with the 5 required tables."""
    db_path = tmp_path / "test_university.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            gender TEXT,
            date_of_birth DATE,
            city TEXT
        );
        CREATE TABLE instructors (
            instructor_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            department TEXT,
            email TEXT
        );
        CREATE TABLE courses (
            course_id INTEGER PRIMARY KEY,
            course_name TEXT NOT NULL,
            credit_hours INTEGER,
            instructor_id INTEGER REFERENCES instructors(instructor_id)
        );
        CREATE TABLE enrollments (
            enrollment_id INTEGER PRIMARY KEY,
            student_id INTEGER REFERENCES students(student_id),
            course_id INTEGER REFERENCES courses(course_id),
            enrollment_date DATE,
            semester TEXT
        );
        CREATE TABLE assessments (
            assessment_id INTEGER PRIMARY KEY,
            enrollment_id INTEGER REFERENCES enrollments(enrollment_id),
            assessment_type TEXT,
            score REAL
        );
    """)

    cur.executemany(
        "INSERT INTO students VALUES (?, ?, ?, ?, ?)",
        [
            (1001, "Ahmed Ali", "Male", "2003-04-15", "Sanaa"),
            (1002, "Sara Mohammed", "Female", "2004-01-20", "Dhamar"),
        ],
    )
    cur.executemany(
        "INSERT INTO instructors VALUES (?, ?, ?, ?)",
        [
            (1, "Dr. Ahmed", "CS", "ahmed@uni.edu"),
            (2, "Dr. Sara", "IT", "sara@uni.edu"),
        ],
    )
    cur.executemany(
        "INSERT INTO courses VALUES (?, ?, ?, ?)",
        [
            (101, "Python", 3, 1),
            (102, "Databases", 3, 2),
        ],
    )
    cur.executemany(
        "INSERT INTO enrollments VALUES (?, ?, ?, ?, ?)",
        [
            (1, 1001, 101, "2026-01-10", "Spring 2026"),
            (2, 1001, 102, "2026-01-10", "Spring 2026"),
            (3, 1002, 101, "2026-01-11", "Spring 2026"),
        ],
    )
    cur.executemany(
        "INSERT INTO assessments VALUES (?, ?, ?, ?)",
        [
            (1, 1, "Midterm", 82.0),
            (2, 1, "Final", 90.0),
            (3, 2, "Midterm", 76.0),
            (4, 3, "Final", 95.0),
        ],
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def builder(mock_db: Path, tmp_path: Path) -> StarSchemaBuilder:
    """StarSchemaBuilder pointed at the mock DB and a tmp output dir."""
    return StarSchemaBuilder(db_path=mock_db, output_dir=tmp_path / "gold")


# ===========================================================================
# parquet_writer — write_parquet
# ===========================================================================

class TestWriteParquet:

    def test_writes_valid_file(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        out = tmp_path / "out.parquet"
        result = write_parquet(sample_df, out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_creates_parent_directories(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        out = tmp_path / "deep" / "nested" / "out.parquet"
        write_parquet(sample_df, out)
        assert out.exists()

    def test_raises_on_empty_dataframe(self, tmp_path: Path) -> None:
        empty = pd.DataFrame(columns=["a", "b"])
        with pytest.raises(ValueError, match="empty"):
            write_parquet(empty, tmp_path / "empty.parquet")

    def test_roundtrip_preserves_data(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        out = tmp_path / "roundtrip.parquet"
        write_parquet(sample_df, out)
        loaded = pd.read_parquet(out)
        assert len(loaded) == len(sample_df)
        assert list(loaded.columns) == list(sample_df.columns)


# ===========================================================================
# parquet_writer — read_parquet
# ===========================================================================

class TestReadParquet:

    def test_reads_back_written_file(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        out = tmp_path / "read.parquet"
        write_parquet(sample_df, out)
        loaded = read_parquet(out)
        assert len(loaded) == len(sample_df)

    def test_reads_column_subset(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        out = tmp_path / "subset.parquet"
        write_parquet(sample_df, out)
        loaded = read_parquet(out, columns=["student_id", "name"])
        assert list(loaded.columns) == ["student_id", "name"]

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_parquet(tmp_path / "missing.parquet")


# ===========================================================================
# parquet_writer — compare + info
# ===========================================================================

class TestCompareAndInfo:

    def test_compare_returns_expected_keys(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        sample_df.to_csv(csv_path, index=False)

        result = compare_csv_vs_parquet(csv_path)
        for key in ("csv_bytes", "parquet_bytes", "ratio",
                    "compression_pct", "rows", "columns"):
            assert key in result

    def test_compare_missing_csv_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            compare_csv_vs_parquet(tmp_path / "missing.csv")

    def test_get_parquet_info_returns_metadata(
        self, sample_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        out = tmp_path / "info.parquet"
        write_parquet(sample_df, out)
        info = get_parquet_info(out)
        assert info["rows"] == 3
        assert info["columns"] == 6
        assert "student_id" in info["column_names"]
        assert "name" in info["column_names"]

    def test_get_info_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            get_parquet_info(tmp_path / "missing.parquet")


# ===========================================================================
# StarSchemaBuilder — setup
# ===========================================================================

class TestStarSchemaBuilderSetup:

    def test_raises_on_missing_db(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            StarSchemaBuilder(
                db_path=tmp_path / "missing.db",
                output_dir=tmp_path / "out",
            )

    def test_creates_output_dir(self, mock_db: Path, tmp_path: Path) -> None:
        out = tmp_path / "new_dir" / "gold"
        StarSchemaBuilder(db_path=mock_db, output_dir=out)
        assert out.exists()

    def test_check_schema_passes_on_valid_db(self, builder: StarSchemaBuilder) -> None:
        builder._check_schema()  # should not raise

    def test_check_schema_raises_on_incomplete_db(self, tmp_path: Path) -> None:
        incomplete = tmp_path / "incomplete.db"
        conn = sqlite3.connect(incomplete)
        conn.execute("CREATE TABLE students (student_id INTEGER)")
        conn.commit()
        conn.close()

        builder = StarSchemaBuilder(db_path=incomplete, output_dir=tmp_path / "out")
        with pytest.raises(ValueError, match="Missing tables"):
            builder._check_schema()


# ===========================================================================
# StarSchemaBuilder — Dimensions
# ===========================================================================

class TestDimensions:

    def test_dim_students(self, builder: StarSchemaBuilder) -> None:
        students = builder._read_table("students")
        dim = builder._build_dim_students(students)

        assert len(dim) == 2
        assert "student_id" in dim.columns
        assert "full_name" in dim.columns
        assert "city" in dim.columns

    def test_dim_courses(self, builder: StarSchemaBuilder) -> None:
        courses = builder._read_table("courses")
        dim = builder._build_dim_courses(courses)

        assert len(dim) == 2
        assert "course_id" in dim.columns
        assert "course_name" in dim.columns
        assert "instructor_id" in dim.columns

    def test_dim_instructors(self, builder: StarSchemaBuilder) -> None:
        instructors = builder._read_table("instructors")
        dim = builder._build_dim_instructors(instructors)

        assert len(dim) == 2
        assert "instructor_id" in dim.columns
        assert "department" in dim.columns

    def test_dim_time(self, builder: StarSchemaBuilder) -> None:
        enrollments = builder._read_table("enrollments")
        dim = builder._build_dim_time(enrollments)

        # 2026-01-10 to 2026-01-11 → 2 days
        assert len(dim) == 2
        expected_cols = {"time_id", "full_date", "year", "month",
                         "day", "weekday", "is_weekend"}
        assert expected_cols.issubset(set(dim.columns))

    def test_dim_time_raises_without_date(self, builder: StarSchemaBuilder) -> None:
        bad_df = pd.DataFrame({"enrollment_id": [1, 2]})
        with pytest.raises(ValueError, match="enrollment_date"):
            builder._build_dim_time(bad_df)


# ===========================================================================
# StarSchemaBuilder — Facts
# ===========================================================================

class TestFacts:

    def test_fact_student_performance(self, builder: StarSchemaBuilder) -> None:
        assessments = builder._read_table("assessments")
        enrollments = builder._read_table("enrollments")
        courses = builder._read_table("courses")

        fact = builder._build_fact_student_performance(assessments, enrollments, courses)

        assert len(fact) == 4  # 4 assessments in fixture
        for col in ("assessment_id", "enrollment_id", "student_id",
                    "course_id", "instructor_id", "score"):
            assert col in fact.columns

    def test_fact_enrollment(self, builder: StarSchemaBuilder) -> None:
        enrollments = builder._read_table("enrollments")
        fact = builder._build_fact_enrollment(enrollments)

        assert len(fact) == 3
        for col in ("enrollment_id", "student_id", "course_id",
                    "time_id", "semester"):
            assert col in fact.columns

    def test_fact_enrollment_has_derived_time_id(self, builder: StarSchemaBuilder) -> None:
        enrollments = builder._read_table("enrollments")
        fact = builder._build_fact_enrollment(enrollments)

        # time_id should be YYYYMMDD as integer
        assert fact["time_id"].iloc[0] == 20260110


# ===========================================================================
# StarSchemaBuilder — End-to-End
# ===========================================================================

class TestBuildAllEndToEnd:

    def test_build_all_produces_6_parquet_files(self, builder: StarSchemaBuilder) -> None:
        outputs = builder.build_all()

        expected_tables = {
            "dim_students",
            "dim_courses",
            "dim_instructors",
            "dim_time",
            "fact_student_performance",
            "fact_enrollment",
        }
        assert set(outputs.keys()) == expected_tables

        for name, path in outputs.items():
            assert path.exists(), f"Missing output: {name}"
            assert path.suffix == ".parquet"

    def test_build_all_returns_valid_dataframes(self, builder: StarSchemaBuilder) -> None:
        outputs = builder.build_all()

        for name, path in outputs.items():
            df = pd.read_parquet(path)
            assert not df.empty, f"Empty DataFrame: {name}"


# ===========================================================================
# Integration test — real university.db (skip if missing)
# ===========================================================================

class TestRealDatabase:
    """Integration test — runs only if data/raw/university.db exists."""

    @pytest.fixture
    def real_builder(self, tmp_path: Path) -> StarSchemaBuilder:
        real_db = Path("data/raw/university.db").resolve()
        if not real_db.exists():
            pytest.skip(f"Real DB not found: {real_db}")
        return StarSchemaBuilder(
            db_path=real_db,
            output_dir=tmp_path / "real_gold",
        )

    def test_real_db_builds_star_schema(self, real_builder: StarSchemaBuilder) -> None:
        outputs = real_builder.build_all()
        assert len(outputs) == 6

        # Verify each file is readable and non-empty
        for name, path in outputs.items():
            df = pd.read_parquet(path)
            assert len(df) > 0, f"Empty table: {name}"