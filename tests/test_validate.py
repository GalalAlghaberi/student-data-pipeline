"""Tests for the Validate Layer."""

from __future__ import annotations

import pandas as pd
import pytest

from src.validate_layer import (
    validate_data,
    validate_schema,
)


class TestValidateSchema:
    def test_passes_with_all_columns(self, valid_df):
        report = validate_schema(valid_df)
        assert report.is_valid
        assert report.missing_columns == ()
        assert report.total_columns == 6

    def test_raises_on_missing_columns(self):
        df = pd.DataFrame({"student_id": [1], "name": ["A"]})
        with pytest.raises(ValueError, match="Missing"):
            validate_schema(df)

    def test_extra_columns_allowed_by_default(self, valid_df):
        valid_df["extra"] = 1
        report = validate_schema(valid_df)
        assert report.is_valid
        assert "extra" in report.extra_columns

    def test_extra_columns_rejected_in_strict_mode(self, valid_df):
        valid_df["extra"] = 1
        with pytest.raises(ValueError, match="Unexpected"):
            validate_schema(valid_df, strict=True)


class TestValidateData:
    def test_passes_on_valid_data(self, valid_df):
        report = validate_data(valid_df)
        assert report.is_valid
        assert report.total_rows == 3
        assert report.unique_ids == 3

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="empty"):
            validate_data(pd.DataFrame())

    def test_raises_on_null_id(self, valid_df):
        valid_df.loc[0, "student_id"] = pd.NA
        with pytest.raises(ValueError, match="student_id"):
            validate_data(valid_df)

    def test_raises_on_duplicate_id(self, valid_df):
        valid_df.loc[1, "student_id"] = valid_df.loc[0, "student_id"]
        with pytest.raises(ValueError, match="duplicate"):
            validate_data(valid_df)

    def test_raises_on_invalid_age(self, valid_df):
        valid_df.loc[0, "age"] = 999
        with pytest.raises(ValueError, match="age"):
            validate_data(valid_df)

    def test_accumulates_multiple_errors(self, valid_df):
        valid_df.loc[0, "age"] = 999
        valid_df.loc[1, "gpa"] = 10.0
        valid_df.loc[2, "attendance"] = 200.0
        with pytest.raises(ValueError) as exc_info:
            validate_data(valid_df)
        msg = str(exc_info.value)
        assert "age" in msg
        assert "gpa" in msg
        assert "attendance" in msg
