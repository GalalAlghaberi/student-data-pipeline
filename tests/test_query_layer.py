"""Tests for the Query Layer (SQL → DataFrame)."""


from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.db_layer import connect
from src.query_layer import load_ml_features, run_query, run_query_file

pytestmark = pytest.mark.db

@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """Create a small SQLite DB with sample data."""
    db_file = tmp_path / "test.db"
    with connect(db_file) as conn:
        conn.executescript("""
            CREATE TABLE students (
                student_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                city TEXT
            );
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL
            );
            CREATE TABLE assessments (
                assessment_id INTEGER PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                score REAL NOT NULL
            );
        """)
        conn.executescript("""
            INSERT INTO students VALUES
                (1001, 'Ahmed', 'Sanaa'),
                (1002, 'Sara',  'Dhamar');
            INSERT INTO enrollments VALUES
                (1, 1001, 101),
                (2, 1001, 102),
                (3, 1002, 101);
            INSERT INTO assessments VALUES
                (1, 1001, 101, 80),
                (2, 1001, 102, 90),
                (3, 1002, 101, 95);
        """)
    return db_file


class TestRunQuery:
    def test_returns_dataframe(self, populated_db: Path):
        with connect(populated_db) as conn:
            df = run_query(conn, "SELECT * FROM students ORDER BY student_id")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ["student_id", "full_name", "city"]

    def test_aggregation_query(self, populated_db: Path):
        with connect(populated_db) as conn:
            df = run_query(
                conn,
                "SELECT student_id, ROUND(AVG(score), 2) AS avg_score "
                "FROM assessments GROUP BY student_id ORDER BY student_id",
            )
        assert len(df) == 2
        assert df["avg_score"].iloc[0] == 85.0

    def test_raises_on_invalid_sql(self, populated_db: Path):
        with connect(populated_db) as conn:
            with pytest.raises(RuntimeError, match="Query failed"):
                run_query(conn, "SELECT * FROM nonexistent_table")


class TestRunQueryFile:
    def test_runs_file_with_comments(self, populated_db: Path, tmp_path: Path):
        sql_file = tmp_path / "query.sql"
        sql_file.write_text(
            "-- This is a comment\n"
            "-- Another comment\n"
            "SELECT student_id, full_name FROM students ORDER BY student_id;\n",
            encoding="utf-8",
        )
        with connect(populated_db) as conn:
            df = run_query_file(conn, sql_file)
        assert len(df) == 2

    def test_raises_on_missing_file(self, populated_db: Path):
        with connect(populated_db) as conn:
            with pytest.raises(FileNotFoundError):
                run_query_file(conn, Path("nonexistent.sql"))

    def test_raises_on_empty_file(self, populated_db: Path, tmp_path: Path):
        sql_file = tmp_path / "empty.sql"
        sql_file.write_text("-- only comment\n", encoding="utf-8")
        with connect(populated_db) as conn:
            with pytest.raises(ValueError, match="No executable SQL"):
                run_query_file(conn, sql_file)


class TestLoadMLFeatures:
    def test_returns_expected_columns(self, populated_db: Path):
        with connect(populated_db) as conn:
            df = load_ml_features(conn)
        expected = {
            "student_id", "student_name", "city",
            "courses_count", "assessments_count",
            "average_score", "highest_score", "lowest_score",
        }
        assert expected.issubset(set(df.columns))

    def test_returns_all_students(self, populated_db: Path):
        with connect(populated_db) as conn:
            df = load_ml_features(conn)
        assert len(df) == 2

    def test_computes_correct_averages(self, populated_db: Path):
        with connect(populated_db) as conn:
            df = load_ml_features(conn).set_index("student_id")
        assert df.loc[1001, "average_score"] == 85.0
        assert df.loc[1002, "average_score"] == 95.0
