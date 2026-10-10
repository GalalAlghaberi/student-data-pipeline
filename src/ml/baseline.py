"""ML Baseline — Phase B (Day 1).

DummyRegressor(strategy="mean") wrapper.

Reference: docs/ML_EXPERIMENTS.md §6.1

Purpose: lower bound. If LinearRegression/Ridge can't beat this on the
same CV scheme, the features carry no linear signal for the target.

The baseline predicts the mean of y_train for every test sample.
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
from sklearn.dummy import DummyRegressor

logger = logging.getLogger(__name__)

STRATEGY: Final = "mean"


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def make_baseline() -> DummyRegressor:
    """Return a fresh DummyRegressor predicting the training mean.

    Returns:
        Configured DummyRegressor(strategy="mean").
    """
    return DummyRegressor(strategy=STRATEGY)


def fit_predict(
    X_train,
    y_train,
    X_test,
) -> np.ndarray:
    """Fit baseline on train, predict on test.

    Args:
        X_train: Train features (ignored by DummyRegressor — kept for API symmetry).
        y_train: Train target.
        X_test: Test features.

    Returns:
        1-D array of predictions (= mean(y_train)).
    """
    model = make_baseline()
    model.fit(X_train, y_train)
    return model.predict(X_test)


# ─────────────────────────────────────────────────────────────
# CLI — Sanity check
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """Sanity check: python -m src.ml.baseline"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from .data import build_feature_matrix, load_features
    from .metrics import compute_all

    df = load_features()
    X, y = build_feature_matrix(df)

    # Quick holdout (illustration only — real evaluation uses CV in pipeline.py)
    X_train, X_test = X.iloc[:6], X.iloc[6:]
    y_train, y_test = y.iloc[:6], y.iloc[6:]

    preds = fit_predict(X_train, y_train, X_test)
    metrics = compute_all(y_test, preds)

    print()
    print("=" * 60)
    print("ML Baseline — Sanity Check (6/3 holdout, illustrative)")
    print("=" * 60)
    print(f"y_train mean: {y_train.mean():.4f}")
    print(f"predictions : {np.round(preds, 4).tolist()}")
    print()
    print("Metrics on held-out 3 rows:")
    for k, v in metrics.items():
        print(f"  {k:5s}: {v:.6f}")


if __name__ == "__main__":
    main()