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


class TestTableExists:
    def test_true_for_existing_table(self, temp_db: Path, schema_file: Path):
        with connect(temp_db) as conn:
            execute_sql_file(conn, schema_file)
            assert table_exists(conn, "users") is True

    def test_false_for_missing_table(self, temp_db: Path):
        with connect(temp_db) as conn:
            assert table_exists(conn, "nonexistent") is False


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
