"""Tests for the I/O Layer (load_data, save_data)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.io_layer import load_data, save_data


class TestLoadData:
    def test_loads_valid_csv(self, raw_csv: Path):
        df = load_data(raw_csv)
        assert len(df) == 3
        assert list(df.columns) == [
            "student_id", "name", "age", "gpa", "attendance", "city",
        ]

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_data(Path("does_not_exist.csv"))

    def test_raises_on_wrong_extension(self, tmp_path: Path):
        wrong = tmp_path / "data.json"
        wrong.write_text("{}")
        with pytest.raises(ValueError, match=r"\.csv"):
            load_data(wrong)

    def test_raises_on_empty_csv(self, tmp_path: Path):
        empty = tmp_path / "empty.csv"
        empty.write_text("")
        with pytest.raises(ValueError):
            load_data(empty)

    def test_raises_on_directory(self, tmp_path: Path):
        with pytest.raises(ValueError, match="not a regular file"):
            load_data(tmp_path)


class TestSaveData:
    def test_saves_csv(self, tmp_path: Path, valid_df):
        out = tmp_path / "out.csv"
        save_data(valid_df, out, verify=False)
        assert out.exists()
        reloaded = pd.read_csv(out)
        assert len(reloaded) == len(valid_df)

    def test_creates_parent_directory(self, tmp_path: Path, valid_df):
        out = tmp_path / "nested" / "deep" / "out.csv"
        save_data(valid_df, out, verify=False)
        assert out.exists()

    def test_verify_success(self, tmp_path: Path, valid_df):
        out = tmp_path / "out.csv"
        save_data(valid_df, out, verify=True)
        assert out.exists()
