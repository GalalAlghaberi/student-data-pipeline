"""Tests for src/ml — Phase B (Day 1).

Coverage:
  - data.py:    loading, leakage-safe matrix, age derivation
  - split.py:   LOO + KFold(3) fold counts
  - metrics.py: mae/rmse/r2 correctness, NaN handling
  - baseline.py: predicts training mean
  - trainer.py: linear/ridge return ndarray
  - pipeline.py: end-to-end shape + non-negative MAE
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.ml import (
    baseline,
    data,
    metrics,
    pipeline,
    split,
    trainer,
)

# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

GOLD_DIR = Path(__file__).resolve().parent.parent / "data" / "gold"
FEATURES_PARQUET = GOLD_DIR / "ml_features.parquet"

pytestmark = pytest.mark.skipif(
    not FEATURES_PARQUET.exists(),
    reason="ml_features.parquet not built (run src.features.engineering)",
)


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return data.load_features(GOLD_DIR)


@pytest.fixture(scope="module")
def XY(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return data.build_feature_matrix(df)


# ─────────────────────────────────────────────────────────────
# data.py
# ─────────────────────────────────────────────────────────────

def test_load_features_shape(df: pd.DataFrame) -> None:
    assert df.shape == (9, 16)  # 15 original + derived `age`


def test_load_features_derives_age(df: pd.DataFrame) -> None:
    assert "age" in df.columns
    assert df["age"].between(16, 80).all()
    assert df["age"].dtype == "Int64"


def test_build_feature_matrix_columns(XY) -> None:
    X, y = XY
    expected = data.FEATURES_NUMERIC + data.FEATURES_CATEGORICAL
    assert list(X.columns) == expected
    assert len(X) == len(y) == 9


def test_build_feature_matrix_excludes_leaky(XY) -> None:
    X, _ = XY
    for col in data.EXCLUDED_LEAKY:
        assert col not in X.columns, f"Leaky column {col!r} leaked into X"


def test_build_feature_matrix_no_nan(XY) -> None:
    X, y = XY
    assert not X.isna().any().any()
    assert not y.isna().any()


def test_get_feature_names_contract() -> None:
    cfg = data.get_feature_names()
    assert cfg["target"] == "gpa"
    assert "avg_score" in cfg["excluded_leaky"]
    assert cfg["reference_date"] == "2026-10-10"


# ─────────────────────────────────────────────────────────────
# split.py
# ─────────────────────────────────────────────────────────────

def test_loo_has_n_folds() -> None:
    cv = split.make_loo_cv()
    info = split.describe_cv(cv, n_samples=9)
    assert info["n_splits"] == 9
    assert info["test_sizes"] == [1]
    assert info["train_sizes"] == [8]


def test_kfold_has_three_folds() -> None:
    cv = split.make_kfold_cv()
    info = split.describe_cv(cv, n_samples=9)
    assert info["n_splits"] == 3
    assert info["test_sizes"] == [3]
    assert info["train_sizes"] == [6]


# ─────────────────────────────────────────────────────────────
# metrics.py
# ─────────────────────────────────────────────────────────────

def test_mae_perfect_is_zero() -> None:
    y = np.array([1.0, 2.0, 3.0])
    assert metrics.mae(y, y) == 0.0


def test_rmse_equals_mae_for_single_sample() -> None:
    y_true = np.array([3.0])
    y_pred = np.array([2.5])
    assert metrics.mae(y_true, y_pred) == 0.5
    assert metrics.rmse(y_true, y_pred) == 0.5


def test_r2_perfect_is_one() -> None:
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert metrics.r2(y, y) == 1.0


def test_r2_returns_nan_for_single_sample() -> None:
    y = np.array([3.0])
    assert np.isnan(metrics.r2(y, y))


def test_aggregate_skips_nan() -> None:
    folds = [
        {"mae": 1.0, "rmse": 1.0, "r2": 1.0},
        {"mae": 3.0, "rmse": 3.0, "r2": float("nan")},
    ]
    agg = metrics.aggregate(folds)
    assert agg["mae"]["mean"] == 2.0
    assert agg["mae"]["n_valid"] == 2
    assert agg["r2"]["mean"] == 1.0
    assert agg["r2"]["n_valid"] == 1


def test_aggregate_empty_raises() -> None:
    with pytest.raises(ValueError):
        metrics.aggregate([])


# ─────────────────────────────────────────────────────────────
# baseline.py
# ─────────────────────────────────────────────────────────────

def test_baseline_predicts_training_mean(XY) -> None:
    X, y = XY
    X_train, y_train = X.iloc[:6], y.iloc[:6]
    X_test = X.iloc[6:]
    preds = baseline.fit_predict(X_train, y_train, X_test)
    assert preds.shape == (3,)
    assert np.allclose(preds, y_train.mean())


# ─────────────────────────────────────────────────────────────
# trainer.py
# ─────────────────────────────────────────────────────────────

def test_linear_returns_ndarray(XY) -> None:
    X, y = XY
    X_num = X[data.FEATURES_NUMERIC]
    preds = trainer.fit_predict_linear(X_num.iloc[:6], y.iloc[:6], X_num.iloc[6:])
    assert isinstance(preds, np.ndarray)
    assert preds.shape == (3,)


def test_ridge_alpha_default() -> None:
    model = trainer.make_ridge()
    assert model.alpha == 1.0


def test_get_trainer_unknown_raises() -> None:
    with pytest.raises(KeyError):
        trainer.get_trainer("nonexistent")


# ─────────────────────────────────────────────────────────────
# pipeline.py
# ─────────────────────────────────────────────────────────────

def test_pipeline_runs_end_to_end() -> None:
    fold_df = pipeline.run_pipeline(GOLD_DIR)
    # 2 CV schemes × 3 models × folds (9 + 3) = 36
    assert len(fold_df) == 36
    assert set(fold_df["cv"]) == {"loo", "kfold3"}
    assert set(fold_df["model"]) == {"baseline", "linear", "ridge"}


def test_summary_has_n_valid_column() -> None:
    fold_df = pipeline.run_pipeline(GOLD_DIR)
    summary = pipeline.summarize(fold_df)
    assert "r2_n_valid" in summary.columns
    loo_rows = summary[summary["cv"] == "loo"]
    assert (loo_rows["r2_n_valid"] == 0).all()
    kf_rows = summary[summary["cv"] == "kfold3"]
    assert (kf_rows["r2_n_valid"] == 3).all()


def test_pipeline_mae_non_negative() -> None:
    fold_df = pipeline.run_pipeline(GOLD_DIR)
    assert (fold_df["mae"] >= 0).all()
    assert (fold_df["rmse"] >= 0).all()


def test_preprocessor_handles_unknown_category(XY) -> None:
    X, _ = XY
    pre = pipeline.build_preprocessor()
    X_train = X.iloc[:6].copy()
    X_test = X.iloc[6:].copy()
    # Inject unseen category in test fold
    X_test.loc[X_test.index[0], "city"] = "UnknownCity"
    pre.fit(X_train)
    X_test_t = pre.transform(X_test)  # must not raise
    assert X_test_t.shape[0] == 3