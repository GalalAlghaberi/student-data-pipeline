"""Tests for the Transform Layer."""

from __future__ import annotations

import pandas as pd
import pytest

from src.transform_layer import clean_data, convert_data_types


class TestConvertDataTypes:
    def test_converts_strings_to_numeric(self, dirty_df):
        result = convert_data_types(dirty_df)
        assert pd.api.types.is_numeric_dtype(result["student_id"])
        assert pd.api.types.is_numeric_dtype(result["age"])

    def test_coerces_invalid_to_nan(self):
        df = pd.DataFrame({
            "student_id": ["1", "abc"],
            "age": ["20", "xyz"],
            "gpa": ["3.5", "not"],
            "attendance": ["90", "??"],
        })
        result = convert_data_types(df)
        assert result["student_id"].isnull().sum() == 1
        assert result["age"].isnull().sum() == 1

    def test_does_not_mutate_input(self, dirty_df):
        original = dirty_df.copy()
        convert_data_types(dirty_df)
        pd.testing.assert_frame_equal(dirty_df, original)

    def test_idempotent(self, dirty_df):
        once = convert_data_types(dirty_df)
        twice = convert_data_types(once)
        pd.testing.assert_frame_equal(once, twice)


class TestCleanData:
    def test_removes_exact_duplicates(self, dirty_df):
        result = clean_data(dirty_df)
        assert len(result) == len(result.drop_duplicates())

    def test_removes_duplicate_ids(self, dirty_df):
        typed = convert_data_types(dirty_df)
        result = clean_data(typed)
        assert result["student_id"].is_unique

    def test_strips_whitespace(self):
        df = pd.DataFrame({
            "student_id": [1],
            "name": ["  Ahmed  "],
            "age": [20],
            "gpa": [3.5],
            "attendance": [90.0],
            "city": ["  sanaa  "],
        })
        result = clean_data(df)
        assert result["name"].iloc[0] == "Ahmed"
        assert result["city"].iloc[0] == "Sanaa"

    def test_handles_outliers(self, dirty_df):
        typed = convert_data_types(dirty_df)
        result = clean_data(typed)
        assert result["age"].between(16, 80).all()
        assert result["gpa"].between(0, 4).all()
        assert result["attendance"].between(0, 100).all()

    def test_does_not_mutate_input(self, dirty_df):
        original = dirty_df.copy()
        clean_data(dirty_df)
        pd.testing.assert_frame_equal(dirty_df, original)

    def test_fills_city_with_unknown(self):
        df = pd.DataFrame({
            "student_id": [1, 2],
            "name": ["A", "B"],
            "age": [20, 21],
            "gpa": [3.5, 3.8],
            "attendance": [90.0, 95.0],
            "city": ["Sanaa", None],
        })
        result = clean_data(df)
        assert "Unknown" in result["city"].values


class TestDefensiveBehavior:
    """
    Document the defensive behavior of clean_data.

    Design decision: clean_data must be safe to call INDEPENDENTLY
    of convert_data_types. When numeric columns still have string dtype,
    clean_data should skip outlier/fill operations on them and log a
    warning — not crash.
    """

    def test_clean_data_alone_does_not_crash_on_string_dtypes(self, dirty_df):
        """clean_data must not raise if called without convert_data_types."""
        result = clean_data(dirty_df)  # should not raise
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_clean_data_warns_on_non_numeric_columns(self, dirty_df, caplog):
        """clean_data should log a warning when skipping non-numeric columns."""
        import logging
        with caplog.at_level(logging.WARNING, logger="src.transform_layer"):
            clean_data(dirty_df)
        messages = [rec.message for rec in caplog.records]
        assert any("not numeric" in msg for msg in messages), (
            f"Expected 'not numeric' warning, got: {messages}"
        )

    def test_full_pipeline_still_handles_outliers(self, dirty_df):
        """After convert_data_types, clean_data MUST remove outliers."""
        typed = convert_data_types(dirty_df)
        result = clean_data(typed)
        # After type conversion + cleaning, no outliers should remain
        assert result["age"].dropna().between(16, 80).all()
        assert result["gpa"].dropna().between(0, 4).all()
        assert result["attendance"].dropna().between(0, 100).all()
