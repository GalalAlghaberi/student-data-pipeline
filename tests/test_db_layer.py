"""Tests for the Database Layer (SQLite connection + SQL execution)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.db_layer import (
    connect,
    count_rows,
    execute_sql_file,
    table_exists,
)

pytestmark = pytest.mark.db


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Return a path to a fresh temp SQLite database."""
    return tmp_path / "test.db"


@pytest.fixture
def schema_file(tmp_path: Path) -> Path:
    """Create a minimal schema file for testing."""
    sql = tmp_path / "schema.sql"
    sql.write_text(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """,
        encoding="utf-8",
    )
    return sql


# ═══════════════════════════════════════════════════════════════
# TestConnect
# ═══════════════════════════════════════════════════════════════

class TestConnect:
    def test_creates_database_file(self, temp_db: Path):
        with connect(temp_db) as conn:
            assert isinstance(conn, sqlite3.Connection)
        assert temp_db.exists()

    def test_creates_parent_directories(self, tmp_path: Path):
        nested = tmp_path / "a" / "b" / "c" / "test.db"
        with connect(nested) as conn:
            pass
        assert nested.exists()

    def test_enforces_foreign_keys(self, temp_db: Path):
        with connect(temp_db) as conn:
            cur = conn.execute("PRAGMA foreign_keys")
            assert cur.fetchone()[0] == 1


# ═══════════════════════════════════════════════════════════════
# TestExecuteSQLFile
# ═══════════════════════════════════════════════════════════════

class TestExecuteSQLFile:
    def test_executes_schema(self, temp_db: Path, schema_file: Path):
        with connect(temp_db) as conn:
            execute_sql_file(conn, schema_file)
            assert table_exists(conn, "users")
            assert table_exists(conn, "posts")

    def test_raises_on_missing_file(self, temp_db: Path):
        with connect(temp_db) as conn:
            with pytest.raises(FileNotFoundError, match="SQL file not found"):
                execute_sql_file(conn, Path("nonexistent.sql"))


# ═══════════════════════════════════════════════════════════════
# TestTableExists
# ═══════════════════════════════════════════════════════════════

class TestTableExists:
    def test_true_for_existing_table(self, temp_db: Path, schema_file: Path):
        with connect(temp_db) as conn:
            execute_sql_file(conn, schema_file)
            assert table_exists(conn, "users") is True

    def test_false_for_missing_table(self, temp_db: Path):
        with connect(temp_db) as conn:
            assert table_exists(conn, "nonexistent") is False


# ═══════════════════════════════════════════════════════════════
# TestCountRows
# ═══════════════════════════════════════════════════════════════

class TestCountRows:
    def test_counts_empty_table(self, temp_db: Path, schema_file: Path):
        with connect(temp_db) as conn:
            execute_sql_file(conn, schema_file)
            assert count_rows(conn, "users") == 0

    def test_counts_populated_table(self, temp_db: Path, schema_file: Path):
        with connect(temp_db) as conn:
            execute_sql_file(conn, schema_file)
            conn.execute("INSERT INTO users (id, name) VALUES (1, 'A'), (2, 'B')")
            conn.commit()
            assert count_rows(conn, "users") == 2

    def test_raises_on_missing_table(self, temp_db: Path):
        with connect(temp_db) as conn:
            with pytest.raises(ValueError, match="does not exist"):
                count_rows(conn, "nonexistent")


# ═══════════════════════════════════════════════════════════════
# Foreign Key Enforcement (Unit 4, pp. 14-15)
# Module-level (not in class) — tmp_path needs pytest discovery
# Regression: prevents accidental use of raw sqlite3.connect()
# ═══════════════════════════════════════════════════════════════

def test_foreign_keys_enabled_on_connect(tmp_path):
    """db_layer.connect() must enable FK enforcement."""
    db_file = tmp_path / "test.db"
    conn = connect(db_file)
    try:
        status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert status == 1, "Foreign key enforcement must be ENABLED"
    finally:
        conn.close()


def test_invalid_foreign_key_is_rejected(tmp_path):
    """Insert with non-existent FK must raise IntegrityError."""
    db_file = tmp_path / "test.db"
    conn = connect(db_file)
    try:
        conn.executescript("""
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY
            );
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );
            INSERT INTO courses VALUES (101);
        """)
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            conn.execute("INSERT INTO enrollments VALUES (99, 999)")
    finally:
        conn.close()


def test_valid_foreign_key_is_accepted(tmp_path):
    """Insert with valid FK must succeed."""
    db_file = tmp_path / "test.db"
    conn = connect(db_file)
    try:
        conn.executescript("""
            CREATE TABLE courses (
                course_id INTEGER PRIMARY KEY
            );
            CREATE TABLE enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );
            INSERT INTO courses VALUES (101);
        """)
        conn.commit()

        conn.execute("INSERT INTO enrollments VALUES (1, 101)")
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
        assert count == 1
    finally:
        conn.close()