"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def valid_df() -> pd.DataFrame:
    """A clean, valid DataFrame that passes all rules."""
    return pd.DataFrame({
        "student_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "age": [20, 21, 22],
        "gpa": [3.5, 3.8, 3.9],
        "attendance": [90.0, 95.0, 87.0],
        "city": ["Riyadh", "Jeddah", "Dammam"],
    })


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    """A messy DataFrame: duplicates, outliers, whitespace, wrong case."""
    return pd.DataFrame({
        "student_id": ["1", "2", "1", "3"],
        "name": ["Alice", "Bob", "Alice", "Charlie"],
        "age": ["20", "150", "20", "22"],
        "gpa": ["3.5", "5.0", "3.5", "3.9"],
        "attendance": ["90", "-10", "90", "87"],
        "city": ["riyadh", "JEDDAH", "riyadh", "dammam"],
    })


@pytest.fixture
def raw_csv(tmp_path, valid_df) -> "Path":
    """Write a valid CSV file to a temporary directory."""
    from pathlib import Path
    csv_path = tmp_path / "students.csv"
    valid_df.to_csv(csv_path, index=False)
    return csv_path
