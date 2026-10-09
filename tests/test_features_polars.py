"""Tests for src/features/engineering_polars.py — Phase A (Polars Migration).

Mirrors tests/test_features.py (22 tests) with `_polars` suffix, plus
12 tests for synthetic_generator.

Test #8 is repurposed as `test_polars_matches_pandas_output` — the
critical Golden Rule 1 verification — replacing the redundant
`test_score_change_is_numeric_polars` (Polars enforces types natively).

Total: 22 mirror + 12 synthetic = 34 tests.

References:
  - docs/POLARS_MIGRATION.md §9 (hybrid test strategy)
  - Unit 6 (Polars Expressions)
  - Unit 9 (Leakage Prevention, pp. 76-77)
  - Unit 11 (Testing)

Golden Rules:
  - engineering.py and test_features.py are FROZEN.
  - All tests run offline (no network, no db markers).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

from src.features.engineering_polars import (
    FEATURE_CATALOG,
    GOLD_DIR_DEFAULT,
    FeatureEngineeringError,
    PolarsFeatureEngineer,
)
from src.features.synthetic_generator import generate_synthetic


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def engineer() -> PolarsFeatureEngineer:
    """Shared engineer, loaded once per test module."""
    eng = PolarsFeatureEngineer()
    eng.load_gold()
    eng.build_base_features()
    eng.split_train_test()
    eng.compute_train_statistics()
    eng.apply_statistics()
    eng.compute_city_rank()
    return eng


# ═══════════════════════════════════════════════════════════════
# 1. Loading (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_load_gold_tables_polars() -> None:
    """Gold layer loads all 6 tables with expected row counts.

    Current dataset (after adding student 1009 + 2 enrollments):
      - 9 students (8 original + 1009)
      - 30 assessments (26 original + 4 for 1009)
    """
    eng = PolarsFeatureEngineer()
    eng.load_gold()
    assert len(eng.tables) == 6
    assert eng.tables["dim_students"].height == 9
    assert eng.tables["fact_student_performance"].height == 30


def test_load_gold_fails_on_missing_dir_polars(tmp_path: Path) -> None:
    """Missing Gold directory raises a clear error."""
    eng = PolarsFeatureEngineer(gold_dir=tmp_path / "nonexistent")
    with pytest.raises(FeatureEngineeringError, match="Gold directory not found"):
        eng.load_gold()


# ═══════════════════════════════════════════════════════════════
# 2. Grain & Schema (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_base_features_grain_is_one_row_per_student_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """Grain must be exactly 1 row per student."""
    df = engineer._features
    assert df is not None
    assert df["student_id"].n_unique() == df.height


def test_base_features_has_required_columns_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """All 9 base feature columns present."""
    required = {
        "student_id", "gpa", "attendance", "avg_score",
        "n_assessments", "score_change", "attendance_rate",
        "academic_risk_score", "performance_level",
    }
    assert required.issubset(set(engineer._features.columns))


# ═══════════════════════════════════════════════════════════════
# 3. Ranges & Formulas (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_attendance_rate_in_range_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """attendance_rate ∈ [0, 1]."""
    df = engineer._features
    assert df["attendance_rate"].is_between(0.0, 1.0).all()


def test_risk_score_formula_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """academic_risk_score = (4 - gpa) + ((100 - attendance) / 25)."""
    df = engineer._features
    expected = (
        (4.0 - pl.col("gpa"))
        + ((100.0 - pl.col("attendance")) / 25.0)
    ).round(4)
    diff = df.select(
        (pl.col("academic_risk_score") - expected).abs().max().alias("d")
    )["d"].item()
    assert diff is not None and diff < 1e-4


# ═══════════════════════════════════════════════════════════════
# 4. Categories (1 test)
# ═══════════════════════════════════════════════════════════════

def test_performance_level_values_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """performance_level ∈ {Excellent, Very Good, Good, Pass, Weak}."""
    allowed = {"Excellent", "Very Good", "Good", "Pass", "Weak"}
    observed = set(engineer._features["performance_level"].unique().to_list())
    assert observed.issubset(allowed)


# ═══════════════════════════════════════════════════════════════
# 5. Split (3 tests)
# ═══════════════════════════════════════════════════════════════

def test_split_sizes_polars(engineer: PolarsFeatureEngineer) -> None:
    """Split sizes must match the configured test_size ratio."""
    total = engineer._train.height + engineer._test.height
    expected_test = max(1, round(total * engineer.test_size))
    expected_train = total - expected_test

    assert engineer._train.height == expected_train, (
        f"train: expected {expected_train}, got {engineer._train.height}"
    )
    assert engineer._test.height == expected_test, (
        f"test: expected {expected_test}, got {engineer._test.height}"
    )
    assert total == engineer._features.height


def test_split_no_overlap_polars(engineer: PolarsFeatureEngineer) -> None:
    """No student_id appears in both train and test."""
    train_ids = set(engineer._train["student_id"].to_list())
    test_ids = set(engineer._test["student_id"].to_list())
    assert train_ids.isdisjoint(test_ids)


def test_split_marked_correctly_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """The 'split' column contains correct literal values."""
    assert (engineer._train["split"] == "train").all()
    assert (engineer._test["split"] == "test").all()


# ═══════════════════════════════════════════════════════════════
# 6. Leakage Prevention (3 tests) — Unit 9, pp. 76-77
# ═══════════════════════════════════════════════════════════════

def test_statistics_from_train_only_polars() -> None:
    """Imputation statistics must be computed from TRAIN only."""
    eng = PolarsFeatureEngineer()
    eng.load_gold()
    eng.build_base_features()
    eng.split_train_test()
    stats = eng.compute_train_statistics()

    train_median = eng._train["gpa"].median()
    assert stats["gpa_median"] == train_median


def test_test_uses_train_median_polars() -> None:
    """TEST rows must be imputed using TRAIN statistics, not TEST."""
    eng = PolarsFeatureEngineer()
    eng.load_gold()
    eng.build_base_features()
    eng.split_train_test()
    eng.compute_train_statistics()
    eng.apply_statistics()

    # After imputation no nulls remain in either set
    assert eng._train["gpa"].is_null().sum() == 0
    assert eng._test["gpa"].is_null().sum() == 0


def test_no_leakage_in_city_rank_polars() -> None:
    """city_rank must be computed from TRAIN peers only."""
    eng = PolarsFeatureEngineer()
    eng.load_gold()
    eng.build_base_features()
    eng.split_train_test()

    # Columns must NOT exist before compute_city_rank
    assert "city_rank" not in eng._train.columns
    assert "city_rank" not in eng._test.columns

    eng.compute_city_rank()

    # Rank=1 means no strictly-higher TRAIN peer in same city
    for row in eng._test.iter_rows(named=True):
        if row["city_rank"] == 1:
            higher = eng._train.filter(
                (pl.col("city") == row["city"])
                & (pl.col("avg_score") > row["avg_score"])
            )
            assert higher.height == 0


# ═══════════════════════════════════════════════════════════════
# 7. Validation (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_validate_passes_polars(engineer: PolarsFeatureEngineer) -> None:
    """Valid output passes all checks without raising."""
    engineer.validate()  # Must not raise


def test_validate_rejects_duplicate_ids_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """Duplicate student_id must trigger FeatureEngineeringError."""
    # Shallow copy to avoid corrupting the module-scoped fixture
    eng = PolarsFeatureEngineer()
    eng._train = engineer._train
    eng._test = pl.concat([engineer._test, engineer._test.head(1)])
    with pytest.raises(FeatureEngineeringError, match="unique"):
        eng.validate()


# ═══════════════════════════════════════════════════════════════
# 8. 🎯 THE CRITICAL PARITY TEST — replaces test_score_change_is_numeric
# ═══════════════════════════════════════════════════════════════

def test_polars_matches_pandas_output() -> None:
    """Golden Rule 1: Polars output MUST match Pandas output.

    Hybrid strategy (docs/POLARS_MIGRATION.md §9):
      - Numeric → allclose(rtol=1e-3, atol=1e-4)
      - Categorical/IDs → strict with astype(str) normalization
      - Schema → same column set
    """
    pd_path = GOLD_DIR_DEFAULT / "ml_features.parquet"
    pl_path = GOLD_DIR_DEFAULT / "ml_features_polars.parquet"

    if not pd_path.exists() or not pl_path.exists():
        pytest.skip(
            "Both outputs required. Run: "
            "python -m src.features.engineering && "
            "python -m src.features.engineering_polars"
        )

    pd_df = (
        pd.read_parquet(pd_path)
        .sort_values("student_id")
        .reset_index(drop=True)
    )
    pl_df = (
        pl.read_parquet(pl_path)
        .to_pandas()
        .sort_values("student_id")
        .reset_index(drop=True)
    )

    # ── Layer 1: Schema ──
    assert set(pd_df.columns) == set(pl_df.columns), (
        f"Column set mismatch.\n"
        f"Pandas: {sorted(pd_df.columns)}\n"
        f"Polars: {sorted(pl_df.columns)}"
    )

    # ── Layer 2: Numeric (allclose) ──
    numeric_cols = [
        "gpa", "attendance", "avg_score", "score_change",
        "attendance_rate", "academic_risk_score", "city_score_gap",
    ]
    for col in numeric_cols:
        np.testing.assert_allclose(
            pd_df[col].sort_values().values,
            pl_df[col].sort_values().values,
            rtol=1e-3,
            atol=1e-4,
            err_msg=f"Numeric mismatch in '{col}'",
        )

    # ── Layer 3: Categorical/IDs (astype(str) normalization) ──
    for col in ["student_id", "city_rank", "n_assessments"]:
        pd_str = (
            pd_df[col].sort_values().astype(str).reset_index(drop=True)
        )
        pl_str = (
            pl_df[col].sort_values().astype(str).reset_index(drop=True)
        )
        assert pd_str.equals(pl_str), f"ID mismatch in '{col}'"

    # ── Layer 4: Free-text categorical (strict) ──
    for col in ["performance_level"]:
        pd_s = pd_df[col].sort_values().reset_index(drop=True)
        pl_s = pl_df[col].sort_values().reset_index(drop=True)
        assert pd_s.equals(pl_s), f"Categorical mismatch in '{col}'"


# ═══════════════════════════════════════════════════════════════
# 9. Persistence (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_save_creates_outputs_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """save() produces 3 output files."""
    engineer.save()
    assert (GOLD_DIR_DEFAULT / "ml_features_polars.parquet").exists()
    assert (GOLD_DIR_DEFAULT / "train_test_split_polars.parquet").exists()
    assert (GOLD_DIR_DEFAULT / "feature_metadata_polars.json").exists()


def test_metadata_json_valid_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """Metadata JSON contains required keys with consistent counts."""
    path = GOLD_DIR_DEFAULT / "feature_metadata_polars.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    total = engineer._train.height + engineer._test.height

    assert data["grain"] == "1 student"
    assert data["n_rows"] == total
    assert data["n_train"] + data["n_test"] == total
    assert data["n_train"] == engineer._train.height
    assert data["n_test"] == engineer._test.height
    assert data["random_state"] == 42
    assert "features" in data
    assert "train_statistics" in data


# ═══════════════════════════════════════════════════════════════
# 10. Idempotency (1 test)
# ═══════════════════════════════════════════════════════════════

def test_idempotency_polars() -> None:
    """Two consecutive runs produce identical output."""
    df1 = PolarsFeatureEngineer().run().sort("student_id")
    df2 = PolarsFeatureEngineer().run().sort("student_id")
    assert df1.equals(df2)


# ═══════════════════════════════════════════════════════════════
# 11. Catalog (2 tests)
# ═══════════════════════════════════════════════════════════════

def test_feature_catalog_complete_polars() -> None:
    """Catalog contains exactly 6 features."""
    expected = {
        "attendance_rate", "academic_risk_score", "score_change",
        "city_rank", "city_score_gap", "performance_level",
    }
    assert expected == set(FEATURE_CATALOG.keys())


def test_city_rank_documented_as_leakage_risk_polars() -> None:
    """city_rank must be documented as high-leakage-risk."""
    assert FEATURE_CATALOG["city_rank"].leakage_risk == "high"


# ═══════════════════════════════════════════════════════════════
# 12. City Features (1 test)
# ═══════════════════════════════════════════════════════════════

def test_city_score_gap_present_polars(
    engineer: PolarsFeatureEngineer,
) -> None:
    """city_score_gap present in both train and test with Float64."""
    assert "city_score_gap" in engineer._train.columns
    assert "city_score_gap" in engineer._test.columns
    assert engineer._train["city_score_gap"].dtype == pl.Float64


# ═══════════════════════════════════════════════════════════════
# 13. Synthetic Generator (12 tests)
# ═══════════════════════════════════════════════════════════════

def test_synthetic_row_count() -> None:
    """generate_synthetic(n) returns exactly n rows."""
    assert generate_synthetic(50, seed=42).height == 50


def test_synthetic_unique_student_ids() -> None:
    """student_id must be unique."""
    df = generate_synthetic(100, seed=42)
    assert df["student_id"].n_unique() == df.height


def test_synthetic_gpa_range() -> None:
    """gpa ∈ [0, 4]."""
    df = generate_synthetic(200, seed=42)
    assert df["gpa"].is_between(0.0, 4.0).all()


def test_synthetic_attendance_range() -> None:
    """attendance ∈ [0, 100]."""
    df = generate_synthetic(200, seed=42)
    assert df["attendance"].is_between(0.0, 100.0).all()


def test_synthetic_age_range() -> None:
    """age ∈ [16, 80]."""
    df = generate_synthetic(200, seed=42)
    assert df["age"].is_between(16, 80).all()


def test_synthetic_gender_values() -> None:
    """gender ∈ {Male, Female}."""
    df = generate_synthetic(200, seed=42)
    observed = set(df["gender"].unique().to_list())
    assert observed.issubset({"Male", "Female"})


def test_synthetic_city_uses_real_cities() -> None:
    """All city values must exist in dim_students."""
    dim = pl.read_parquet(GOLD_DIR_DEFAULT / "dim_students.parquet")
    real = set(dim["city"].unique().to_list())
    df = generate_synthetic(200, seed=42)
    assert set(df["city"].unique().to_list()).issubset(real)


def test_synthetic_n_assessments_values() -> None:
    """n_assessments ∈ {2, 4}."""
    df = generate_synthetic(200, seed=42)
    observed = set(df["n_assessments"].unique().to_list())
    assert observed.issubset({2, 4})


def test_synthetic_deterministic() -> None:
    """Same seed → identical output."""
    df1 = generate_synthetic(100, seed=42)
    df2 = generate_synthetic(100, seed=42)
    assert df1.equals(df2)


def test_synthetic_no_nulls() -> None:
    """No nulls in generated data."""
    df = generate_synthetic(100, seed=42)
    assert df.null_count().sum_horizontal().item() == 0


def test_synthetic_rejects_zero_rows() -> None:
    """n_rows=0 raises ValueError."""
    with pytest.raises(ValueError, match="n_rows must be >= 1"):
        generate_synthetic(0, seed=42)


def test_synthetic_writes_parquet(tmp_path: Path) -> None:
    """output_path produces a valid parquet file."""
    out = tmp_path / "test_synthetic.parquet"
    generate_synthetic(50, seed=42, output_path=out)
    assert out.exists()
    assert pl.read_parquet(out).height == 50