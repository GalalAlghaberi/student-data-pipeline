"""ML v2 tests — Phase B.7 (Scale-Up).

Covers data_v2.py (B.7.2). Subsequent sections (split_v2, trainer_v2,
pipeline_v2) will add tests in later sub-steps.

Reference: docs/ML_EXPERIMENTS_SCALE.md §3, §4, §9
"""
from __future__ import annotations

import numpy as np
import pytest

from src.ml import data_v2
from src.ml import split_v2
from src.ml import trainer_v2


# ═══════════════════════════════════════════════════════════════
# Test 1 — UCI-only row count
# ═══════════════════════════════════════════════════════════════

def test_load_uci_only_returns_1044():
    """Silver dataset filter must yield exactly 1,044 UCI rows."""
    df = data_v2.load_uci_only()
    assert len(df) == 1044
    assert set(df["source"].unique()) == {"uci"}


# ═══════════════════════════════════════════════════════════════
# Test 2 — no NaN target in UCI rows
# ═══════════════════════════════════════════════════════════════

def test_load_uci_only_no_nan_gpa():
    """UCI rows must have complete gpa (unlike api/postgres/sqlite)."""
    df = data_v2.load_uci_only()
    assert df["gpa"].notna().all()
    assert df["gpa"].between(0.0, 4.0).all()
    assert df["student_id"].notna().all()


# ═══════════════════════════════════════════════════════════════
# Test 3 — leaky columns never appear in any FS
# ═══════════════════════════════════════════════════════════════

@pytest.mark.parametrize("fs", ["A", "B"])
def test_no_leaky_features_in_fs(fs):
    """score_final and score_change must be absent from FS-A and FS-B."""
    df = data_v2.load_uci_only()
    X, _, _ = data_v2.build_feature_matrix_v2(df, fs=fs)
    forbidden = set(data_v2.EXCLUDED_LEAKY)
    assert forbidden.isdisjoint(set(X.columns)), (
        f"Leaky columns leaked into FS-{fs}: "
        f"{sorted(forbidden & set(X.columns))}"
    )


# ═══════════════════════════════════════════════════════════════
# Test 4 — feature-set shapes (5 vs 7 columns)
# ═══════════════════════════════════════════════════════════════

def test_fs_a_has_5_features():
    """FS-A = 2 numeric + 3 categorical."""
    df = data_v2.load_uci_only()
    X, y, groups = data_v2.build_feature_matrix_v2(df, fs="A")
    assert X.shape == (1044, 5)
    assert y.shape == (1044,)
    assert groups.shape == (1044,)
    assert list(X.columns) == [
        "attendance_rate", "age", "gender", "city", "course",
    ]


def test_fs_b_has_7_features():
    """FS-B = FS-A + score_1 + score_2."""
    df = data_v2.load_uci_only()
    X, _, _ = data_v2.build_feature_matrix_v2(df, fs="B")
    assert X.shape == (1044, 7)
    assert list(X.columns) == [
        "attendance_rate", "age", "score_1", "score_2",
        "gender", "city", "course",
    ]


# ═══════════════════════════════════════════════════════════════
# Test 5 — groups column has 662 unique students
# ═══════════════════════════════════════════════════════════════

def test_groups_has_662_unique_students():
    """student_id must have exactly 662 unique values (GroupKFold groups)."""
    df = data_v2.load_uci_only()
    _, _, groups = data_v2.build_feature_matrix_v2(df, fs="A")
    assert groups.nunique() == 662
    # Every student has at least one record
    assert groups.value_counts().min() >= 1
    # 369 multi-record students (from UCI_ETL.md §3.4)
    n_multi = int((groups.value_counts() >= 2).sum())
    assert n_multi == 369


# ═══════════════════════════════════════════════════════════════
# B.7.3 — split_v2 tests
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def uci_df():
    """Load UCI-only DataFrame (module-scoped for speed)."""
    return data_v2.load_uci_only()


@pytest.fixture(scope="module")
def Xy_groups(uci_df):
    """Return (X, y, groups) for FS-A."""
    return data_v2.build_feature_matrix_v2(uci_df, fs="A")


# ─── GroupKFold(5) ──────────────────────────────────────────────

def test_group_kfold_5_yields_5_folds(Xy_groups):
    """GroupKFold(5) must produce exactly 5 folds."""
    X, y, groups = Xy_groups
    cv = split_v2.make_group_kfold_5()
    splits = list(cv.split(X, y, groups=groups))
    assert len(splits) == 5


def test_group_kfold_5_no_leakage(Xy_groups):
    """CRITICAL: no student_id appears in both train and test."""
    X, y, groups = Xy_groups
    cv = split_v2.make_group_kfold_5()
    stats = split_v2.assert_no_group_leakage(cv, X, y, groups)
    assert stats["n_folds"] == 5
    # Every fold must have non-empty train and test
    for f in stats["fold_stats"]:
        assert f["n_train"] > 0
        assert f["n_test"] > 0
        assert f["n_train_groups"] > 0
        assert f["n_test_groups"] > 0


# ─── GroupKFold(3) ──────────────────────────────────────────────

def test_group_kfold_3_yields_3_folds(Xy_groups):
    """GroupKFold(3) must produce exactly 3 folds."""
    X, y, groups = Xy_groups
    cv = split_v2.make_group_kfold_3()
    splits = list(cv.split(X, y, groups=groups))
    assert len(splits) == 3


def test_group_kfold_3_no_leakage(Xy_groups):
    """Stability check: GroupKFold(3) also enforces group isolation."""
    X, y, groups = Xy_groups
    cv = split_v2.make_group_kfold_3()
    stats = split_v2.assert_no_group_leakage(cv, X, y, groups)
    assert stats["n_folds"] == 3


# ─── KFold(5) — the leak demonstration ──────────────────────────

def test_kfold_5_yields_5_folds(Xy_groups):
    """KFold(5) must produce exactly 5 folds."""
    X, y, _ = Xy_groups
    cv = split_v2.make_kfold_5()
    splits = list(cv.split(X, y))
    assert len(splits) == 5


def test_kfold_5_balanced_folds(Xy_groups):
    """KFold(5) splits 1,044 rows into {208, 209}-sized test folds."""
    X, y, _ = Xy_groups
    cv = split_v2.make_kfold_5()
    test_sizes = [len(te) for _, te in cv.split(X, y)]
    assert all(s in (208, 209) for s in test_sizes), test_sizes
    assert sum(test_sizes) == 1044


# ─── LeaveOneOut (v1 bridge) ────────────────────────────────────

def test_loo_yields_1044_folds(Xy_groups):
    """LOO on 1,044 rows produces 1,044 folds of size (1043, 1)."""
    X, y, _ = Xy_groups
    cv = split_v2.make_loo()
    splits = list(cv.split(X, y))
    assert len(splits) == 1044
    assert all(len(te) == 1 for _, te in splits)
    assert all(len(tr) == 1043 for tr, _ in splits)


# ─── describe_cv metadata ───────────────────────────────────────

def test_describe_cv_group_kfold_5(Xy_groups):
    """describe_cv returns correct metadata for GroupKFold(5).

    Note: train_sizes and test_sizes are UNIQUE sizes (a sorted set),
    not per-fold sizes. GroupKFold(5) on 1,044 rows yields:
      - unique train sizes: [835, 836]
      - unique test sizes:  [208, 209]
    """
    X, y, groups = Xy_groups
    cv = split_v2.make_group_kfold_5()
    info = split_v2.describe_cv(cv, n_samples=len(X), groups=groups)
    assert info["type"] == "GroupKFold"
    assert info["n_splits"] == 5
    assert info["n_samples"] == 1044
    assert info["train_sizes"] == [835, 836]
    assert info["test_sizes"] == [208, 209]


def test_describe_cv_without_groups(Xy_groups):
    """describe_cv works for non-group splitters (KFold)."""
    X, y, _ = Xy_groups
    cv = split_v2.make_kfold_5()
    info = split_v2.describe_cv(cv, n_samples=len(X))
    assert info["type"] == "KFold"
    assert info["n_splits"] == 5


# ─── Registry + determinism ─────────────────────────────────────

def test_cv_registry_complete():
    """CV_SCHEMES must contain exactly the 4 documented schemes."""
    assert set(split_v2.CV_SCHEMES.keys()) == {
        "group_kfold_5", "kfold_5", "loo", "group_kfold_3",
    }
    assert split_v2.GROUP_AWARE_SCHEMES == frozenset({
        "group_kfold_5", "group_kfold_3",
    })


def test_kfold_5_deterministic(Xy_groups):
    """Same random_state → identical splits across calls."""
    X, y, _ = Xy_groups
    cv1 = split_v2.make_kfold_5()
    cv2 = split_v2.make_kfold_5()
    splits1 = [te.tolist() for _, te in cv1.split(X, y)]
    splits2 = [te.tolist() for _, te in cv2.split(X, y)]
    assert splits1 == splits2


# ═══════════════════════════════════════════════════════════════
# B.7.4 — trainer_v2 tests
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def numeric_holdout(uci_df):
    """Return (X_train, y_train, X_test, y_test) using numeric-only features.

    No OneHot is applied — keeps trainer mechanics tests fast and
    independent of the encoding pipeline (which lives in pipeline_v2).
    """
    numeric_cols = ["attendance_rate", "age", "score_1", "score_2"]
    X = uci_df[numeric_cols].to_numpy(dtype=float)
    y = uci_df["gpa"].to_numpy(dtype=float)
    split = int(len(X) * 0.8)
    return X[:split], y[:split], X[split:], y[split:]


# ─── Registry ──────────────────────────────────────────────────

def test_trainers_v2_registry_complete():
    """TRAINERS_V2 must contain exactly the 4 documented learners."""
    assert set(trainer_v2.TRAINERS_V2.keys()) == {
        "linear", "ridge", "rf", "gbm",
    }


def test_get_trainer_v2_unknown_raises():
    """get_trainer_v2 raises KeyError on unknown name."""
    with pytest.raises(KeyError, match="Unknown trainer"):
        trainer_v2.get_trainer_v2("nonexistent")


# ─── RandomForest ──────────────────────────────────────────────

def test_rf_yields_finite_predictions(numeric_holdout):
    """RandomForest predictions must be finite (no NaN/Inf)."""
    X_train, y_train, X_test, _ = numeric_holdout
    preds = trainer_v2.fit_predict_rf(X_train, y_train, X_test)
    assert preds.shape == (len(X_test),)
    assert np.isfinite(preds).all()


def test_rf_deterministic(numeric_holdout):
    """Same random_state -> RF predictions agree within float epsilon.

    Note: RandomForestRegressor(n_jobs=-1) uses parallel reduction,
    which can reorder floating-point additions. Assertions therefore
    allow ~1e-12 tolerance (not byte-exact) while still catching any
    real nondeterminism (e.g., unseeded randomness, missing random_state).
    """
    X_train, y_train, X_test, _ = numeric_holdout
    p1 = trainer_v2.fit_predict_rf(X_train, y_train, X_test)
    p2 = trainer_v2.fit_predict_rf(X_train, y_train, X_test)
    np.testing.assert_allclose(p1, p2, rtol=1e-12, atol=1e-12)


# ─── GradientBoosting ──────────────────────────────────────────

def test_gbm_yields_finite_predictions(numeric_holdout):
    """GradientBoosting predictions must be finite (no NaN/Inf)."""
    X_train, y_train, X_test, _ = numeric_holdout
    preds = trainer_v2.fit_predict_gbm(X_train, y_train, X_test)
    assert preds.shape == (len(X_test),)
    assert np.isfinite(preds).all()


def test_gbm_deterministic(numeric_holdout):
    """Same random_state -> GBM predictions agree within float epsilon.

    GBM is single-threaded but we use allclose for consistency with
    test_rf_deterministic and to be robust to future parallelization.
    """
    X_train, y_train, X_test, _ = numeric_holdout
    p1 = trainer_v2.fit_predict_gbm(X_train, y_train, X_test)
    p2 = trainer_v2.fit_predict_gbm(X_train, y_train, X_test)
    np.testing.assert_allclose(p1, p2, rtol=1e-12, atol=1e-12)


# ─── Feature importance ────────────────────────────────────────

def test_extract_feature_importance_rf(numeric_holdout):
    """extract_feature_importance returns dict with correct keys."""
    X_train, y_train, _, _ = numeric_holdout
    numeric_cols = ["attendance_rate", "age", "score_1", "score_2"]
    rf = trainer_v2.make_random_forest()
    rf.fit(X_train, y_train)

    imps = trainer_v2.extract_feature_importance(rf, numeric_cols)
    assert set(imps.keys()) == set(numeric_cols)
    assert all(0.0 <= v <= 1.0 for v in imps.values())
    # Sum of Gini importances is ~1.0
    assert abs(sum(imps.values()) - 1.0) < 1e-6