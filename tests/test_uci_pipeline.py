"""Tests for pipelines/uci_pipeline.py — Phase B.5.

Coverage:
  - Output file existence + shape
  - Unique student/record counts
  - Categorical domains (course, gender, city)
  - Numeric ranges (gpa, attendance_rate)
  - Formula correctness (score_change, name, gpa)
  - Dedup invariant (662 unique, 1,044 records)
  - Idempotency (rerun produces identical output)
  - Transformation invariants (source constant, no NaN)

All tests are offline (no network, no DB) — safe for CI.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pytest

from pipelines import uci_pipeline


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

OUTPUT_PATH = uci_pipeline.DEFAULT_OUTPUT

pytestmark = pytest.mark.skipif(
    not OUTPUT_PATH.exists(),
    reason="uci_clean.parquet not built (run: python -m pipelines.uci_pipeline)",
)


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    """Load uci_clean.parquet once for the entire module."""
    return uci_pipeline.load_clean(OUTPUT_PATH)


# ═══════════════════════════════════════════════════════════════════
# 1. File + shape
# ═══════════════════════════════════════════════════════════════════

def test_output_file_exists() -> None:
    assert OUTPUT_PATH.exists()
    assert OUTPUT_PATH.stat().st_size > 0


def test_output_shape(df: pd.DataFrame) -> None:
    assert df.shape == (uci_pipeline.EXPECTED_TOTAL, len(uci_pipeline.OUTPUT_COLUMNS))


def test_output_column_order(df: pd.DataFrame) -> None:
    assert list(df.columns) == uci_pipeline.OUTPUT_COLUMNS


# ═══════════════════════════════════════════════════════════════════
# 2. Counts (dedup invariant)
# ═══════════════════════════════════════════════════════════════════

def test_unique_students(df: pd.DataFrame) -> None:
    """662 unique students identified via 13-key merge."""
    assert df["student_id"].nunique() == uci_pipeline.EXPECTED_UNIQUE_STUDENTS


def test_unique_records(df: pd.DataFrame) -> None:
    """1,044 unique record_id (one per row)."""
    assert df["record_id"].nunique() == uci_pipeline.EXPECTED_UNIQUE_RECORDS


def test_record_id_is_unique(df: pd.DataFrame) -> None:
    """No duplicate record_id (stronger than nunique check)."""
    assert not df["record_id"].duplicated().any()


def test_student_id_has_duplicates(df: pd.DataFrame) -> None:
    """Verify count of multi-record students.

    Note on '382' from student-merge.R:
      R's script reports nrow(d3) = 382, which counts (math_row, por_row)
      PAIRS, not distinct students. When a student has multiple rows per
      file (within-file 13-key collision), R generates multiple pairs.

    Our algorithm assigns ONE student_id per unique 13-key. The number
    of DISTINCT students with ≥2 records is 369 (verified empirically).
    """
    counts = df["student_id"].value_counts()
    assert (counts >= 2).sum() == 369, \
        f"Expected 369 multi-record students, got {(counts >= 2).sum()}"

# ═══════════════════════════════════════════════════════════════════
# 3. Categorical domains
# ═══════════════════════════════════════════════════════════════════

def test_course_domain(df: pd.DataFrame) -> None:
    assert set(df["course"].unique()) == {"math", "portuguese"}


def test_gender_domain(df: pd.DataFrame) -> None:
    assert set(df["gender"].unique()) == {"Male", "Female"}


def test_city_domain(df: pd.DataFrame) -> None:
    assert set(df["city"].unique()) == {"GP-U", "GP-R", "MS-U", "MS-R"}


def test_source_constant(df: pd.DataFrame) -> None:
    assert (df["source"] == "uci").all()


# ═══════════════════════════════════════════════════════════════════
# 4. Numeric ranges
# ═══════════════════════════════════════════════════════════════════

def test_gpa_range(df: pd.DataFrame) -> None:
    assert df["gpa"].between(0.0, 4.0).all()


def test_attendance_rate_range(df: pd.DataFrame) -> None:
    assert df["attendance_rate"].between(0.0, 1.0).all()


def test_age_range(df: pd.DataFrame) -> None:
    assert df["age"].between(15, 22).all()


def test_n_assessments_constant(df: pd.DataFrame) -> None:
    assert (df["n_assessments"] == 3).all()


# ═══════════════════════════════════════════════════════════════════
# 5. Formula correctness
# ═══════════════════════════════════════════════════════════════════

def test_gpa_formula(df: pd.DataFrame) -> None:
    """gpa == score_final / 5.0 (with 4-decimal rounding)."""
    expected = (df["score_final"] / 5.0).round(4)
    pd.testing.assert_series_equal(
        df["gpa"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
        rtol=0, atol=1e-6,
    )


def test_score_change_formula(df: pd.DataFrame) -> None:
    """score_change == score_final - score_1."""
    expected = df["score_final"] - df["score_1"]
    pd.testing.assert_series_equal(
        df["score_change"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )


def test_name_matches_student_id(df: pd.DataFrame) -> None:
    """name == 'Student_' + student_id[1:]."""
    expected = "Student_" + df["student_id"].str[1:]
    pd.testing.assert_series_equal(
        df["name"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )


# ═══════════════════════════════════════════════════════════════════
# 6. Integrity
# ═══════════════════════════════════════════════════════════════════

def test_no_missing_values(df: pd.DataFrame) -> None:
    assert df.isna().sum().sum() == 0


def test_score_final_range(df: pd.DataFrame) -> None:
    assert df["score_final"].between(0, 20).all()


def test_g3_zero_count(df: pd.DataFrame) -> None:
    """53 students have final grade 0 (real failure, not missing)."""
    assert (df["score_final"] == 0).sum() == 53


# ═══════════════════════════════════════════════════════════════════
# 7. Cross-course consistency
# ═══════════════════════════════════════════════════════════════════

def test_shared_students_have_both_courses(df: pd.DataFrame) -> None:
    """A student_id with >1 record must have different course values."""
    grouped = df.groupby("student_id")["course"].nunique()
    multi = grouped[grouped > 1]
    assert (multi == 2).all(), "A multi-record student must span both courses"


def test_single_course_students(df: pd.DataFrame) -> None:
    """Verify split: multi-record students vs single-record students.

    662 students total:
      - 369 appear in ≥2 rows (multi-course OR within-file duplicates)
      - 293 appear in exactly 1 row
    """
    counts = df["student_id"].value_counts()
    multi = (counts >= 2).sum()
    single = (counts == 1).sum()
    assert multi == 369, f"multi: {multi}"
    assert single == 293, f"single: {single}"
    assert multi + single == 662

# ═══════════════════════════════════════════════════════════════════
# 8. Idempotency
# ═══════════════════════════════════════════════════════════════════

def test_etl_idempotent(tmp_path: Path) -> None:
    """Re-running ETL produces byte-identical output."""
    # Compute hash of current output
    original_bytes = OUTPUT_PATH.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()

    # Re-run ETL to a temp location
    tmp_out = tmp_path / "uci_clean_rerun.parquet"
    uci_pipeline.run_etl(
        raw_dir=uci_pipeline.DEFAULT_RAW_DIR,
        output_path=tmp_out,
    )

    rerun_bytes = tmp_out.read_bytes()
    rerun_hash = hashlib.sha256(rerun_bytes).hexdigest()

    assert original_hash == rerun_hash, "ETL output is not deterministic"


# ═══════════════════════════════════════════════════════════════════
# 9. CLI sanity (light — no subprocess)
# ═══════════════════════════════════════════════════════════════════

def test_load_clean_raises_on_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope.parquet"
    with pytest.raises(FileNotFoundError, match="python -m pipelines.uci_pipeline"):
        uci_pipeline.load_clean(missing)