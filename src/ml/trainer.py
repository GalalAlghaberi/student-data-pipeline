"""ML Trainers — Phase B (Day 1).

LinearRegression + Ridge(α=1.0) wrappers with a common interface.

Reference: docs/ML_EXPERIMENTS.md §6.2–6.3

Why Ridge?
  - N=9 is too small for unregularized OLS (unstable coefficients).
  - Ridge α=1.0 adds L2 penalty — documented default (no tuning in Day 1).
  - We report both to show the regularization gap honestly.

API symmetry:
  Each trainer exposes `make_*()` and `fit_predict_*()` so that
  pipeline.py can loop over a registry of {name: (make, fit_predict)}.

Naming note:
  `fit_predict` (without suffix) is reserved for baseline.py only.
  Trainers use explicit suffixes: `_linear` and `_ridge`.
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
from sklearn.linear_model import LinearRegression, Ridge

logger = logging.getLogger(__name__)

RIDGE_ALPHA: Final = 1.0


# ─────────────────────────────────────────────────────────────
# LinearRegression
# ─────────────────────────────────────────────────────────────

def make_linear() -> LinearRegression:
    """Return a fresh LinearRegression (unregularized OLS)."""
    return LinearRegression()


def fit_predict_linear(X_train, y_train, X_test) -> np.ndarray:
    """Fit LinearRegression on train, predict on test."""
    model = make_linear()
    model.fit(X_train, y_train)
    return model.predict(X_test)


# ─────────────────────────────────────────────────────────────
# Ridge
# ─────────────────────────────────────────────────────────────

def make_ridge(alpha: float = RIDGE_ALPHA) -> Ridge:
    """Return a fresh Ridge with L2 penalty.

    Args:
        alpha: Regularization strength (default 1.0 — see §6.3).
    """
    return Ridge(alpha=alpha, random_state=None)


def fit_predict_ridge(X_train, y_train, X_test) -> np.ndarray:
    """Fit Ridge on train, predict on test."""
    model = make_ridge()
    model.fit(X_train, y_train)
    return model.predict(X_test)


# ─────────────────────────────────────────────────────────────
# Registry (used by pipeline.py)
# ─────────────────────────────────────────────────────────────

TRAINERS: Final[dict] = {
    "linear": fit_predict_linear,
    "ridge": fit_predict_ridge,
}


def get_trainer(name: str):
    """Return a fit_predict callable by name.

    Args:
        name: one of {"linear", "ridge"}.

    Raises:
        KeyError: if name is not registered.
    """
    if name not in TRAINERS:
        raise KeyError(
            f"Unknown trainer: {name!r}. Available: {sorted(TRAINERS)}"
        )
    return TRAINERS[name]


# ─────────────────────────────────────────────────────────────
# CLI — Sanity check
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """Sanity check: python -m src.ml.trainer"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from .data import build_feature_matrix, load_features
    from .metrics import compute_all

    df = load_features()
    X, y = build_feature_matrix(df)

    # Drop categorical for this sanity check (sklearn LinearRegression
    # cannot handle string columns without encoding — encoding is
    # introduced later in pipeline.py via ColumnTransformer).
    X_num = X[["attendance_rate", "n_assessments", "score_change", "age"]]

    # Illustrative 6/3 holdout
    X_train, X_test = X_num.iloc[:6], X_num.iloc[6:]
    y_train, y_test = y.iloc[:6], y.iloc[6:]

    print()
    print("=" * 60)
    print("ML Trainers — Sanity Check (6/3 holdout, numeric only)")
    print("=" * 60)

    for name, fn in TRAINERS.items():
        preds = fn(X_train, y_train, X_test)
        metrics = compute_all(y_test, preds)
        print(f"\n[{name}]")
        print(f"  predictions: {np.round(preds, 4).tolist()}")
        for k, v in metrics.items():
            print(f"  {k:5s}: {v:.6f}")


if __name__ == "__main__":
    main()