"""Tests for the Storage Layer (SQLite)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.storage_layer import save_to_sqlite, _assert_safe_identifier


class TestSafeIdentifier:
    def test_accepts_valid_names(self):
        _assert_safe_identifier("students")
        _assert_safe_identifier("student_data")
        _assert_safe_identifier("_private")
        _assert_safe_identifier("Table123")

    def test_rejects_invalid_names(self):
        with pytest.raises(ValueError):
            _assert_safe_identifier("students; DROP TABLE users")
        with pytest.raises(ValueError):
            _assert_safe_identifier("123table")
        with pytest.raises(ValueError):
            _assert_safe_identifier("my-table")
        with pytest.raises(ValueError):
            _assert_safe_identifier("")


class TestSaveToSqlite:
    def test_saves_data(self, tmp_path: Path, valid_df):
        db = tmp_path / "test.db"
        save_to_sqlite(valid_df, db)
        assert db.exists()

        with sqlite3.connect(db) as conn:
            result = pd.read_sql("SELECT * FROM students", conn)
            assert len(result) == len(valid_df)

    def test_creates_indexes(self, tmp_path: Path, valid_df):
        db = tmp_path / "test.db"
        save_to_sqlite(valid_df, db, create_indexes=True)

        with sqlite3.connect(db) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = [row[0] for row in cur.fetchall()]
            assert "idx_students_student_id" in indexes
            assert "idx_students_city" in indexes

    def test_replaces_existing_table(self, tmp_path: Path, valid_df):
        db = tmp_path / "test.db"
        save_to_sqlite(valid_df, db)

        smaller_df = valid_df.head(1).copy()
        save_to_sqlite(smaller_df, db)

        with sqlite3.connect(db) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM students")
            assert cur.fetchone()[0] == 1

    def test_rejects_unsafe_table_name(self, tmp_path: Path, valid_df):
        db = tmp_path / "test.db"
        with pytest.raises(ValueError, match="Unsafe"):
            save_to_sqlite(valid_df, db, table_name="bad;name")
