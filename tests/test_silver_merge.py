"""Tests for src/warehouse/silver_merge.py — Phase B.6.

Coverage:
  - Output files exist + shape
  - Schema contract (17 columns, order)
  - Sources present (8 expected)
  - record_id uniqueness + source-prefix format
  - Non-null guarantees
  - Numeric ranges where present
  - Transform invariants (attendance → rate, UCI record_id regen)
  - Quality report validity
  - Idempotency
  - Error handling (missing parquet)

All tests are offline — safe for CI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.warehouse import silver_merge


# ═══════════════════════════════════════════════════════════════════
# Constants + fixtures
# ═══════════════════════════════════════════════════════════════════

OUTPUT_DIR = silver_merge.DEFAULT_OUTPUT_DIR
PARQUET_PATH = OUTPUT_DIR / silver_merge.OUTPUT_PARQUET
REPORT_PATH = OUTPUT_DIR / silver_merge.OUTPUT_REPORT

EXPECTED_TOTAL = 1_121
EXPECTED_SOURCES = {
    "uci", "api", "csv", "json", "mongodb",
    "postgres", "scraper", "sqlite",
}

pytestmark = pytest.mark.skipif(
    not PARQUET_PATH.exists(),
    reason="silver parquet not built (run: python -m src.warehouse.silver_merge)",
)


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return silver_merge.load_unified(OUTPUT_DIR)


@pytest.fixture(scope="module")
def report() -> dict:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════════════
# 1. Files + shape
# ═══════════════════════════════════════════════════════════════════

def test_parquet_exists() -> None:
    assert PARQUET_PATH.exists()
    assert PARQUET_PATH.stat().st_size > 0


def test_report_exists() -> None:
    assert REPORT_PATH.exists()
    assert REPORT_PATH.stat().st_size > 0


def test_shape(df: pd.DataFrame) -> None:
    assert df.shape == (EXPECTED_TOTAL, len(silver_merge.UNIFIED_COLUMNS))


def test_column_order(df: pd.DataFrame) -> None:
    assert list(df.columns) == silver_merge.UNIFIED_COLUMNS


# ═══════════════════════════════════════════════════════════════════
# 2. Sources
# ═══════════════════════════════════════════════════════════════════

def test_all_sources_present(df: pd.DataFrame) -> None:
    assert set(df["source"].dropna().unique()) == EXPECTED_SOURCES


def test_uci_row_count(df: pd.DataFrame) -> None:
    assert (df["source"] == "uci").sum() == 1_044


def test_source_prefix_in_record_id(df: pd.DataFrame) -> None:
    """Every record_id must start with R-<source>-."""
    for src in EXPECTED_SOURCES:
        subset = df[df["source"] == src]
        assert subset["record_id"].str.startswith(f"R-{src}-").all(), \
            f"record_id format broken for source={src}"


# ═══════════════════════════════════════════════════════════════════
# 3. Integrity
# ═══════════════════════════════════════════════════════════════════

def test_record_id_unique(df: pd.DataFrame) -> None:
    assert not df["record_id"].duplicated().any()


def test_non_null_columns(df: pd.DataFrame) -> None:
    for col in silver_merge.NON_NULL_COLUMNS:
        assert df[col].notna().all(), f"{col} has NaN"


def test_gpa_range_where_present(df: pd.DataFrame) -> None:
    present = df[df["gpa"].notna()]
    assert present["gpa"].between(0.0, 4.0).all()


def test_attendance_range_where_present(df: pd.DataFrame) -> None:
    present = df[df["attendance_rate"].notna()]
    assert present["attendance_rate"].between(0.0, 1.0).all()


def test_gpa_nan_count(df: pd.DataFrame) -> None:
    """46 NaN = 30 (api) + 8 (postgres) + 8 (sqlite)."""
    assert df["gpa"].isna().sum() == 46


def test_attendance_nan_count(df: pd.DataFrame) -> None:
    assert df["attendance_rate"].isna().sum() == 46


# ═══════════════════════════════════════════════════════════════════
# 4. Transform invariants
# ═══════════════════════════════════════════════════════════════════

def test_uci_gpa_fully_populated(df: pd.DataFrame) -> None:
    uci = df[df["source"] == "uci"]
    assert uci["gpa"].notna().all()
    assert uci["attendance_rate"].notna().all()


def test_uci_course_preserved(df: pd.DataFrame) -> None:
    uci = df[df["source"] == "uci"]
    assert set(uci["course"].unique()) == {"math", "portuguese"}


def test_base_sources_have_no_course(df: pd.DataFrame) -> None:
    base = df[df["source"] != "uci"]
    assert base["course"].isna().all()
    assert base["gender"].isna().all()
    assert base["score_final"].isna().all()


def test_base_attendance_converted_to_rate(df: pd.DataFrame) -> None:
    """Base sources: attendance (0-100) → attendance_rate (0-1)."""
    base = df[(df["source"] != "uci") & (df["attendance_rate"].notna())]
    assert base["attendance_rate"].between(0.0, 1.0).all()
    # At least one row where rate < 1.0 (not all are 100%)
    assert (base["attendance_rate"] < 1.0).any()


# ═══════════════════════════════════════════════════════════════════
# 5. Quality report
# ═══════════════════════════════════════════════════════════════════

def test_report_total_rows(report: dict) -> None:
    assert report["total_rows"] == EXPECTED_TOTAL


def test_report_total_columns(report: dict) -> None:
    assert report["total_columns"] == len(silver_merge.UNIFIED_COLUMNS)


def test_report_sources_complete(report: dict) -> None:
    assert set(report["sources"].keys()) == EXPECTED_SOURCES


def test_report_column_coverage(report: dict) -> None:
    cov = report["column_coverage"]
    assert set(cov.keys()) == set(silver_merge.UNIFIED_COLUMNS)
    for col in silver_merge.NON_NULL_COLUMNS:
        assert cov[col] == 1.0, f"{col} coverage should be 100%"


# ═══════════════════════════════════════════════════════════════════
# 6. Idempotency + errors
# ═══════════════════════════════════════════════════════════════════

def test_merge_idempotent(tmp_path: Path) -> None:
    """Re-running merge to a temp dir produces byte-identical parquet."""
    original_hash = hashlib.sha256(PARQUET_PATH.read_bytes()).hexdigest()

    silver_merge.run_merge(
        processed_dir=silver_merge.DEFAULT_PROCESSED_DIR,
        output_dir=tmp_path,
    )

    rerun_hash = hashlib.sha256(
        (tmp_path / silver_merge.OUTPUT_PARQUET).read_bytes()
    ).hexdigest()

    assert original_hash == rerun_hash, "merge output not deterministic"


def test_load_unified_raises_on_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="silver_merge"):
        silver_merge.load_unified(tmp_path)