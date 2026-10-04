"""Validate Layer — Guards (return None or raise)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from src.config import (
    OUTLIER_RANGES,
    REQUIRED_COLUMNS,
    REQUIRED_NON_NULL,
    UNIQUE_COLUMNS,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchemaReport:
    is_valid: bool
    missing_columns: tuple[str, ...]
    extra_columns: tuple[str, ...]
    total_columns: int


@dataclass(frozen=True)
class ValidationReport:
    is_valid: bool
    errors: tuple[str, ...]
    total_rows: int
    unique_ids: int

    def summary(self) -> str:
        if self.is_valid:
            return f"Valid: {self.total_rows} rows, {self.unique_ids} unique IDs."
        return f"Invalid: {len(self.errors)} error(s)."


def validate_schema(
    df: pd.DataFrame,
    strict: bool = False,
) -> SchemaReport:
    """Validate the structural schema of the DataFrame."""
    required = REQUIRED_COLUMNS
    actual = set(df.columns)

    missing = tuple(sorted(required - actual))
    extra = tuple(sorted(actual - required))

    if missing:
        raise ValueError(
            f"Schema validation failed.\n"
            f"  Missing : {list(missing)}\n"
            f"  Required: {sorted(required)}\n"
            f"  Found   : {sorted(actual)}"
        )

    if strict and extra:
        raise ValueError(f"Unexpected columns (strict mode): {list(extra)}")

    if extra:
        logger.warning("Extra columns detected: %s", list(extra))

    report = SchemaReport(
        is_valid=True,
        missing_columns=(),
        extra_columns=extra,
        total_columns=df.shape[1],
    )
    logger.info("Schema validation passed (%d columns).", df.shape[1])
    return report


def validate_data(df: pd.DataFrame) -> ValidationReport:
    """
    Comprehensive final validation.
    Accumulates all errors before raising.
    """
    errors: list[str] = []

    # 1. Structure
    if df.empty:
        errors.append("Dataset is empty.")

    # 2. Completeness
    for col in REQUIRED_NON_NULL:
        if col not in df.columns:
            continue
        n = int(df[col].isnull().sum())
        if n > 0:
            errors.append(f"{col}: {n} NULL value(s) found.")

    # 3. Uniqueness
    for col in UNIQUE_COLUMNS:
        if col not in df.columns:
            continue
        n = int(df[col].duplicated().sum())
        if n > 0:
            errors.append(f"{col}: {n} duplicate value(s) found.")

    # 4. Ranges
    for col, (lo, hi) in OUTLIER_RANGES.items():
        if col not in df.columns:
            continue
        mask = ~df[col].between(lo, hi)
        n = int(mask.sum())
        if n > 0:
            examples = df.loc[mask, col].head(3).tolist()
            errors.append(
                f"{col}: {n} value(s) outside [{lo}, {hi}]. "
                f"Examples: {examples}"
            )

    unique_ids = 0
    if "student_id" in df.columns and not df.empty:
        unique_ids = int(df["student_id"].nunique())

    report = ValidationReport(
        is_valid=not errors,
        errors=tuple(errors),
        total_rows=len(df),
        unique_ids=unique_ids,
    )

    if errors:
        raise ValueError(
            "Validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    logger.info("Data validation passed. %s", report.summary())
    return report
