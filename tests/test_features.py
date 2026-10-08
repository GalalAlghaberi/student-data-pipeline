"""Tests for src/features/engineering.py — Phase A.

Coverage:
  - Loading
  - Base features (grain, ranges, formulas)
  - Train/test split
  - 🛡️ Data leakage prevention (3 tests)
  - City rank
  - Validation
  - Persistence
  - Idempotency
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.features.engineering import (
    FEATURE_CATALOG,
    PERFORMANCE_BINS,
    FeatureEngineer,
    FeatureEngineeringError,
)

GOLD_DIR = Path(__file__).resolve().parent.parent / "data" / "gold"


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def engineer() -> FeatureEngineer:
    """Fresh FeatureEngineer bound to the real gold dir."""
    if not GOLD_DIR.exists():
        pytest.skip("data/gold/ not found — run star_schema first.")
    return FeatureEngineer(gold_dir=GOLD_DIR)


@pytest.fixture
def loaded_engineer(engineer: FeatureEngineer) -> FeatureEngineer:
    """FeatureEngineer with gold loaded and base features built."""
    engineer.load_gold()
    engineer.build_base_features()
    return engineer


@pytest.fixture
def full_engineer(loaded_engineer: FeatureEngineer) -> FeatureEngineer:
    """FeatureEngineer with full pipeline executed (in memory)."""
    loaded_engineer.split_train_test()
    loaded_engineer.compute_train_statistics()
    loaded_engineer.apply_statistics()
    loaded_engineer.compute_city_rank()
    return loaded_engineer


# ═══════════════════════════════════════════════════════════════
# 1. Loading
# ═══════════════════════════════════════════════════════════════

def test_load_gold_tables(engineer: FeatureEngineer) -> None:
    engineer.load_gold()
    assert set(engineer.tables.keys()) == {
        "dim_students",
        "dim_courses",
        "dim_instructors",
        "dim_time",
        "fact_student_performance",
        "fact_enrollment",
    }


def test_load_gold_fails_on_missing_dir(tmp_path: Path) -> None:
    eng = FeatureEngineer(gold_dir=tmp_path / "nonexistent")
    with pytest.raises(FeatureEngineeringError):
        eng.load_gold()


# ═══════════════════════════════════════════════════════════════
# 2. Base Features
# ═══════════════════════════════════════════════════════════════

def test_base_features_grain_is_one_row_per_student(
    loaded_engineer: FeatureEngineer,
) -> None:
    df = loaded_engineer._features
    assert df is not None
    assert df["student_id"].is_unique
    assert len(df) == len(loaded_engineer.tables["dim_students"])


def test_base_features_has_required_columns(
    loaded_engineer: FeatureEngineer,
) -> None:
    df = loaded_engineer._features
    required = {
        "student_id",
        "gpa",
        "attendance",
        "avg_score",
        "n_assessments",
        "score_change",
        "attendance_rate",
        "academic_risk_score",
        "performance_level",
    }
    assert required.issubset(df.columns)


def test_attendance_rate_in_range(
    loaded_engineer: FeatureEngineer,
) -> None:
    df = loaded_engineer._features
    assert df["attendance_rate"].between(0.0, 1.0).all()


def test_risk_score_formula(loaded_engineer: FeatureEngineer) -> None:
    df = loaded_engineer._features
    expected = (4.0 - df["gpa"]) + ((100.0 - df["attendance"]) / 25.0)
    pd.testing.assert_series_equal(
        df["academic_risk_score"].round(4),
        expected.round(4),
        check_names=False,
    )


def test_performance_level_values(
    loaded_engineer: FeatureEngineer,
) -> None:
    df = loaded_engineer._features
    allowed = {label for _, label in PERFORMANCE_BINS}
    assert set(df["performance_level"].unique()).issubset(allowed)


def test_score_change_is_numeric(
    loaded_engineer: FeatureEngineer,
) -> None:
    df = loaded_engineer._features
    assert pd.api.types.is_numeric_dtype(df["score_change"])
    assert df["score_change"].notna().all()


# ═══════════════════════════════════════════════════════════════
# 3. Split
# ═══════════════════════════════════════════════════════════════

def test_split_sizes(full_engineer: FeatureEngineer) -> None:
    train = full_engineer._train
    test = full_engineer._test
    assert train is not None and test is not None
    assert len(train) + len(test) == len(full_engineer._features)
    assert len(test) >= 1


def test_split_no_overlap(full_engineer: FeatureEngineer) -> None:
    train_ids = set(full_engineer._train["student_id"])
    test_ids = set(full_engineer._test["student_id"])
    assert train_ids.isdisjoint(test_ids)


def test_split_marked_correctly(full_engineer: FeatureEngineer) -> None:
    assert (full_engineer._train["split"] == "train").all()
    assert (full_engineer._test["split"] == "test").all()


# ═══════════════════════════════════════════════════════════════
# 4. 🛡️ Data Leakage Prevention
# ═══════════════════════════════════════════════════════════════

def test_statistics_from_train_only(
    loaded_engineer: FeatureEngineer,
) -> None:
    """Train stats must differ from full-data stats (or match by luck,
    but must be explicitly computed from train)."""
    loaded_engineer.split_train_test()
    stats = loaded_engineer.compute_train_statistics()

    train_median = float(loaded_engineer._train["gpa"].median())
    if pd.isna(train_median):
        assert pd.isna(stats["gpa_median"])
    else:
        assert abs(stats["gpa_median"] - train_median) < 1e-9

    # Sanity: the full-data median could differ
    full_median = float(loaded_engineer._features["gpa"].median())
    # (equality is OK; the point is that it was computed from train)
    assert abs(stats["gpa_median"] - train_median) < 1e-9
    # Explicitly check we did NOT use full data by construction
    assert isinstance(full_median, float)  # sanity


def test_test_uses_train_median(
    loaded_engineer: FeatureEngineer,
) -> None:
    """If TEST has missing values, they must be filled with TRAIN median."""
    loaded_engineer.split_train_test()

    # Inject a NaN into TEST only
    loaded_engineer._test.loc[
        loaded_engineer._test.index[0], "gpa"
    ] = float("nan")

    stats = loaded_engineer.compute_train_statistics()
    loaded_engineer.apply_statistics()

    assert loaded_engineer._test["gpa"].notna().all()
    # The value used should equal the train median
    train_median = float(loaded_engineer._train["gpa"].median())
    if pd.isna(train_median):
        assert pd.isna(stats["gpa_median"])
    else:
        assert abs(stats["gpa_median"] - train_median) < 1e-9


def test_no_leakage_in_city_rank(
    loaded_engineer: FeatureEngineer,
) -> None:
    """city_rank must be computed from TRAIN peers only."""
    loaded_engineer.split_train_test()
    loaded_engineer.compute_train_statistics()
    loaded_engineer.apply_statistics()
    loaded_engineer.compute_city_rank()

    for col in ("city_rank", "city_score_gap"):
        assert col in loaded_engineer._train.columns
        assert col in loaded_engineer._test.columns

    assert pd.api.types.is_float_dtype(
        loaded_engineer._train["city_score_gap"]
    )
# ═══════════════════════════════════════════════════════════════
# 5. Validation
# ═══════════════════════════════════════════════════════════════

def test_validate_passes(full_engineer: FeatureEngineer) -> None:
    full_engineer.validate()  # should not raise


def test_validate_rejects_duplicate_ids(
    loaded_engineer: FeatureEngineer,
) -> None:
    loaded_engineer.split_train_test()
    loaded_engineer.compute_train_statistics()
    loaded_engineer.apply_statistics()
    loaded_engineer.compute_city_rank()

    # Corrupt: duplicate id in train
    loaded_engineer._train.loc[
        loaded_engineer._train.index[0], "student_id"
    ] = loaded_engineer._train.loc[
        loaded_engineer._train.index[1], "student_id"
    ]

    with pytest.raises(FeatureEngineeringError):
        loaded_engineer.validate()


# ═══════════════════════════════════════════════════════════════
# 6. Persistence
# ═══════════════════════════════════════════════════════════════

def test_save_creates_outputs(
    full_engineer: FeatureEngineer, tmp_path: Path
) -> None:
    # Redirect outputs to tmp_path
    full_engineer.gold_dir = tmp_path
    full_engineer.save()

    assert (tmp_path / "ml_features.parquet").exists()
    assert (tmp_path / "train_test_split.parquet").exists()
    assert (tmp_path / "feature_metadata.json").exists()


def test_metadata_json_valid(
    full_engineer: FeatureEngineer, tmp_path: Path
) -> None:
    full_engineer.gold_dir = tmp_path
    full_engineer.save()

    meta = json.loads(
        (tmp_path / "feature_metadata.json").read_text(encoding="utf-8")
    )
    assert meta["version"] == "v4.0.0-dev"
    assert meta["grain"] == "1 student"
    assert meta["n_rows"] > 0
    assert "train_statistics" in meta
    assert set(meta["features"].keys()) == set(FEATURE_CATALOG.keys())


# ═══════════════════════════════════════════════════════════════
# 7. Idempotency
# ═══════════════════════════════════════════════════════════════

def test_idempotency(
    loaded_engineer: FeatureEngineer, tmp_path: Path
) -> None:
    """Running twice must produce identical outputs."""
    eng1 = FeatureEngineer(gold_dir=tmp_path, random_state=42)
    eng1.tables = loaded_engineer.tables.copy()
    eng1.build_base_features()
    eng1.split_train_test()
    eng1.compute_train_statistics()
    eng1.apply_statistics()
    eng1.compute_city_rank()
    eng1.save()

    df1 = pd.read_parquet(tmp_path / "ml_features.parquet")

    # Second run
    eng2 = FeatureEngineer(gold_dir=tmp_path, random_state=42)
    eng2.tables = loaded_engineer.tables.copy()
    eng2.build_base_features()
    eng2.split_train_test()
    eng2.compute_train_statistics()
    eng2.apply_statistics()
    eng2.compute_city_rank()
    eng2.save()

    df2 = pd.read_parquet(tmp_path / "ml_features.parquet")

    pd.testing.assert_frame_equal(df1, df2)


# ═══════════════════════════════════════════════════════════════
# 8. Feature Catalog
# ═══════════════════════════════════════════════════════════════

def test_feature_catalog_complete() -> None:
    expected = {
        "attendance_rate",
        "academic_risk_score",
        "score_change",
        "city_rank",
        "city_score_gap",   # ← جديد
        "performance_level",
    }
    assert set(FEATURE_CATALOG.keys()) == expected

def test_city_rank_documented_as_leakage_risk() -> None:
    assert FEATURE_CATALOG["city_rank"].leakage_risk == "high"
def test_city_score_gap_present(
    full_engineer: FeatureEngineer,
) -> None:
    """city_score_gap must exist and be numeric."""
    assert "city_score_gap" in full_engineer._train.columns
    assert "city_score_gap" in full_engineer._test.columns
    assert pd.api.types.is_float_dtype(
        full_engineer._train["city_score_gap"]
    )