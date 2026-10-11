"""ML Trainers v2 — Phase B.7 (Scale-Up).

Adds tree-based learners to the v1 linear/ridge models:
  - Reused (unchanged from v1): LinearRegression, Ridge(alpha=1.0)
  - New (this module):          RandomForestRegressor, GradientBoostingRegressor

Reference: docs/ML_EXPERIMENTS_SCALE.md §6

Contract (identical to v1 trainer.py):
  Each learner exposes:
    make_<name>(**kwargs) -> sklearn estimator
    fit_predict_<name>(X_train, y_train, X_test) -> np.ndarray

Baseline is NOT registered here — pipeline_v2 handles DummyRegressor
specially (it ignores X entirely).

Hyperparameters:
  Defaults chosen for B.7 baseline; n_estimators / max_depth /
  learning_rate tuning is deferred to B.8 (documented as non-goal in §1).

Golden Rules:
  - Add a layer; do not replace (v1 trainer.py stays FROZEN).
  - Deterministic (random_state=42).
  - Inputs are already encoded (OneHot applied per fold in pipeline_v2).
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

# Reuse v1 factories unchanged (Golden Rule 1: add, don't replace)
from .trainer import (
    RIDGE_ALPHA,
    fit_predict_linear,
    fit_predict_ridge,
    make_linear,
    make_ridge,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration (deterministic)
# ═══════════════════════════════════════════════════════════════

RANDOM_STATE: Final = 42

# RandomForest defaults
RF_N_ESTIMATORS: Final = 200
RF_MIN_SAMPLES_LEAF: Final = 2

# GradientBoosting defaults
GBM_N_ESTIMATORS: Final = 200
GBM_LEARNING_RATE: Final = 0.05
GBM_MAX_DEPTH: Final = 3


# ═══════════════════════════════════════════════════════════════
# RandomForestRegressor
# ═══════════════════════════════════════════════════════════════

def make_random_forest(
    random_state: int = RANDOM_STATE,
) -> RandomForestRegressor:
    """Return a fresh RandomForestRegressor with B.7 defaults.

    Args:
        random_state: Fixed seed for reproducibility (default 42).

    Returns:
        Configured RandomForestRegressor.
    """
    return RandomForestRegressor(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=None,
        min_samples_leaf=RF_MIN_SAMPLES_LEAF,
        random_state=random_state,
        n_jobs=-1,
    )


def fit_predict_rf(X_train, y_train, X_test) -> np.ndarray:
    """Fit RandomForest on train, predict on test."""
    model = make_random_forest()
    model.fit(X_train, y_train)
    return model.predict(X_test)


# ═══════════════════════════════════════════════════════════════
# GradientBoostingRegressor
# ═══════════════════════════════════════════════════════════════

def make_gradient_boosting(
    random_state: int = RANDOM_STATE,
) -> GradientBoostingRegressor:
    """Return a fresh GradientBoostingRegressor with B.7 defaults.

    Args:
        random_state: Fixed seed for reproducibility (default 42).

    Returns:
        Configured GradientBoostingRegressor.
    """
    return GradientBoostingRegressor(
        n_estimators=GBM_N_ESTIMATORS,
        learning_rate=GBM_LEARNING_RATE,
        max_depth=GBM_MAX_DEPTH,
        random_state=random_state,
    )


def fit_predict_gbm(X_train, y_train, X_test) -> np.ndarray:
    """Fit GradientBoosting on train, predict on test."""
    model = make_gradient_boosting()
    model.fit(X_train, y_train)
    return model.predict(X_test)


# ═══════════════════════════════════════════════════════════════
# Registry (used by pipeline_v2)
# ═══════════════════════════════════════════════════════════════

# 4 learners — baseline handled specially in pipeline_v2
TRAINERS_V2: Final[dict] = {
    "linear": fit_predict_linear,
    "ridge":  fit_predict_ridge,
    "rf":     fit_predict_rf,
    "gbm":    fit_predict_gbm,
}


def get_trainer_v2(name: str):
    """Return a fit_predict callable by name.

    Args:
        name: one of {"linear", "ridge", "rf", "gbm"}.

    Raises:
        KeyError: if name is not registered.
    """
    if name not in TRAINERS_V2:
        raise KeyError(
            f"Unknown trainer: {name!r}. Available: {sorted(TRAINERS_V2)}"
        )
    return TRAINERS_V2[name]


# ═══════════════════════════════════════════════════════════════
# Feature importance extraction (RF, GBM)
# ═══════════════════════════════════════════════════════════════

def extract_feature_importance(
    model,
    feature_names: list[str],
) -> dict[str, float]:
    """Extract feature importances from a fitted tree model.

    Works for RandomForestRegressor and GradientBoostingRegressor.

    Args:
        model:         A fitted sklearn estimator with `.feature_importances_`.
        feature_names: Names matching the columns used to fit the model.

    Returns:
        Dict {feature_name: importance} sorted descending.

    Raises:
        AttributeError: if model does not expose `.feature_importances_`.
        ValueError:     if len(feature_names) != len(model.feature_importances_).
    """
    if not hasattr(model, "feature_importances_"):
        raise AttributeError(
            f"{type(model).__name__} does not expose `.feature_importances_`. "
            "Only tree-based models (RF, GBM) support this."
        )

    importances = np.asarray(model.feature_importances_)
    if len(importances) != len(feature_names):
        raise ValueError(
            f"Length mismatch: model has {len(importances)} importances, "
            f"feature_names has {len(feature_names)}"
        )

    pairs = sorted(
        zip(feature_names, importances.tolist()),
        key=lambda kv: kv[1],
        reverse=True,
    )
    return dict(pairs)


# ═══════════════════════════════════════════════════════════════
# CLI — Sanity check
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Sanity check: python -m src.ml.trainer_v2.

    Uses numeric-only features (no OneHot) to keep the sanity simple.
    Full encoding pipeline lives in pipeline_v2.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from .data_v2 import load_uci_only

    df = load_uci_only()
    numeric_cols = ["attendance_rate", "age", "score_1", "score_2"]
    X = df[numeric_cols].to_numpy(dtype=float)
    y = df["gpa"].to_numpy(dtype=float)

    # Simple 4/5 | 1/5 holdout — illustrative only
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print()
    print("=" * 70)
    print("ML Trainers v2 — Sanity Check (numeric-only holdout)")
    print("=" * 70)
    print(f"n_train: {len(X_train):,}  |  n_test: {len(X_test):,}")
    print()

    for name, fn in TRAINERS_V2.items():
        preds = fn(X_train, y_train, X_test)
        mae = float(np.mean(np.abs(y_test - preds)))
        rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))
        print(f"[{name:6s}]  MAE={mae:.4f}  RMSE={rmse:.4f}")

    print()
    print("Feature importance (RF, numeric-only):")
    rf = make_random_forest()
    rf.fit(X_train, y_train)
    for feat, imp in extract_feature_importance(rf, numeric_cols).items():
        print(f"  {feat:18s} {imp:.4f}")

    print()
    print("Registry entries:")
    for name in TRAINERS_V2:
        print(f"  {name}")


if __name__ == "__main__":
    main()