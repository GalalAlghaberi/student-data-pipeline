"""Transform Layer — Pure, immutable transformations (return DataFrame)."""

from __future__ import annotations

import logging

import pandas as pd

from src.config import (
    FILL_WITH_MEDIAN,
    MISSING_POLICY,
    NUMERIC_COLUMNS,
    OUTLIER_RANGES,
    TARGET_DTYPES,
    TEXT_FIELDS_TO_STRIP,
    TEXT_FIELDS_TO_TITLE,
)

logger = logging.getLogger(__name__)


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce numeric columns to declared dtypes.
    Invalid values → NaN (not silently dropped).
    """
    df = df.copy()
    coerced_summary: dict[str, int] = {}

    for column in NUMERIC_COLUMNS:
        before_na = int(df[column].isnull().sum())

        numeric = pd.to_numeric(df[column], errors="coerce")

        # For Int64, reject decimals instead of silently truncating
        if TARGET_DTYPES[column] == "Int64":
            mask_non_int = numeric.notna() & (numeric % 1 != 0)
            if mask_non_int.any():
                logger.warning(
                    "Column '%s': %d non-integer values → NaN.",
                    column,
                    int(mask_non_int.sum()),
                )
                numeric = numeric.mask(mask_non_int)

        df[column] = numeric.astype(TARGET_DTYPES[column])

        coerced = int(df[column].isnull().sum()) - before_na
        if coerced > 0:
            coerced_summary[column] = coerced

    if coerced_summary:
        logger.warning("Coerced to NaN: %s", coerced_summary)

    return df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicates + duplicate student_ids (with lineage log)."""
    before = len(df)

    df = df.drop_duplicates()
    removed_exact = before - len(df)
    if removed_exact > 0:
        logger.info("Removed %d exact duplicate rows.", removed_exact)

    if "student_id" in df.columns:
        duplicated_mask = df.duplicated(subset=["student_id"], keep="first")
        if duplicated_mask.any():
            dropped_ids = df.loc[duplicated_mask, "student_id"].tolist()
            logger.warning(
                "Duplicate student_ids removed: %s",
                dropped_ids[:10],
            )
            df = df.loc[~duplicated_mask]

    return df


def _clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace, apply title case where appropriate."""
    for col in TEXT_FIELDS_TO_STRIP:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()

    for col in TEXT_FIELDS_TO_TITLE:
        if col in df.columns:
            df[col] = df[col].str.title()

    return df


def _handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace out-of-range values with pd.NA.

    Skips columns that are not numeric (defensive — clean_data
    should work even if convert_data_types was not called first).
    """
    for col, (lo, hi) in OUTLIER_RANGES.items():
        if col not in df.columns:
            continue

        # Skip non-numeric columns (defensive)
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(
                "Column '%s' is not numeric (dtype=%s); skipping outlier check.",
                col, df[col].dtype,
            )
            continue

        mask = ~df[col].between(lo, hi)
        n_outliers = int(mask.sum())
        if n_outliers > 0:
            logger.warning(
                "Column '%s': %d outliers outside [%s, %s] → NA.",
                col, n_outliers, lo, hi,
            )
            df[col] = df[col].where(~mask, pd.NA)

    return df


def _fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the documented missing-value policy per column.

    Skips numeric fill for columns that are not numeric (defensive —
    clean_data should work even if convert_data_types was not called).
    """
    # 1. Drop rows where name is null
    if MISSING_POLICY.get("name") == "drop" and "name" in df.columns:
        n_before = len(df)
        df = df.dropna(subset=["name"])
        dropped = n_before - len(df)
        if dropped > 0:
            logger.info("Dropped %d rows with missing 'name'.", dropped)

    # 2. Fill city with "Unknown"
    if MISSING_POLICY.get("city") == "fill_unknown" and "city" in df.columns:
        n_missing = int(df["city"].isnull().sum())
        if n_missing > 0:
            df["city"] = df["city"].fillna("Unknown")
            logger.info("Filled %d missing 'city' with 'Unknown'.", n_missing)

    # 3. Fill numeric columns with median
    for col in FILL_WITH_MEDIAN:
        if col not in df.columns:
            continue

        # Skip non-numeric columns (defensive)
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(
                "Column '%s' is not numeric (dtype=%s); skipping median fill.",
                col, df[col].dtype,
            )
            continue

        median = df[col].median()
        if pd.isna(median):
            logger.warning("Column '%s' entirely NaN; skipped fill.", col)
            continue

        n_filled = int(df[col].isnull().sum())
        if n_filled > 0:
            df[col] = df[col].fillna(median)
            logger.info(
                "Filled %d values in '%s' with median (%.2f).",
                n_filled, col, float(median),
            )

    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    End-to-end cleaning pipeline (immutable — always copies first).
    """
    logger.info("Cleaning started. Initial shape: %s", df.shape)

    df = df.copy()
    df = _remove_duplicates(df)
    df = _clean_text_fields(df)
    df = _handle_outliers(df)
    df = _fill_missing(df)

    logger.info("Cleaning complete. Final shape: %s", df.shape)
    return df
