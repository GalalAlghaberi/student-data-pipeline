"""ML Metrics Layer — Phase B (Day 1).

MAE / RMSE / R² computed uniformly across CV folds.

Reference: docs/ML_EXPERIMENTS.md §7

Why three metrics?
  - MAE:  intuitive (GPA points, same unit as target).
  - RMSE: penalizes large errors (sensitive to outliers).
  - R²:   normalized against the mean baseline.

All metrics are aggregated as (mean, std) across CV folds.
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

logger = logging.getLogger(__name__)

METRIC_NAMES: Final[tuple[str, ...]] = ("mae", "rmse", "r2")


# ─────────────────────────────────────────────────────────────
# Core metric functions (single fold)
# ─────────────────────────────────────────────────────────────

def mae(y_true, y_pred) -> float:
    """Mean Absolute Error (GPA points)."""
    return float(mean_absolute_error(y_true, y_pred))


def rmse(y_true, y_pred) -> float:
    """Root Mean Squared Error (GPA points)."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def r2(y_true, y_pred) -> float:
    """R² score (unitless). May be negative for small N."""
    return float(r2_score(y_true, y_pred))


def compute_all(y_true, y_pred) -> dict[str, float]:
    """Return {mae, rmse, r2} for one fold."""
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "r2": r2(y_true, y_pred),
    }


# ─────────────────────────────────────────────────────────────
# Aggregation across CV folds
# ─────────────────────────────────────────────────────────────

def aggregate(fold_metrics: list[dict[str, float]]) -> dict[str, dict]:
    """Aggregate a list of fold metric dicts into {metric: {mean, std}}.

    Args:
        fold_metrics: One dict per fold (output of `compute_all`).

    Returns:
        {
          "mae":  {"mean": ..., "std": ...},
          "rmse": {"mean": ..., "std": ...},
          "r2":   {"mean": ..., "std": ...},
          "n_folds": int,
        }
    """
    if not fold_metrics:
        raise ValueError("fold_metrics is empty")

    out: dict[str, dict] = {}
    for name in METRIC_NAMES:
        values = np.array([fm[name] for fm in fold_metrics], dtype=float)
        out[name] = {
            "mean": float(values.mean()),
            "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        }
    out["n_folds"] = len(fold_metrics)
    return out


# ─────────────────────────────────────────────────────────────
# CLI — Sanity check
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """Sanity check: python -m src.ml.metrics"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # Tiny fixed example — perfect prediction should give 0/0/1
    y_true = np.array([3.32, 3.69, 2.96, 3.45, 2.75])
    y_pred_perfect = y_true.copy()
    y_pred_baseline = np.full_like(y_true, y_true.mean())

    print()
    print("=" * 60)
    print("ML Metrics Layer — Sanity Check")
    print("=" * 60)

    print("\nPerfect prediction (expect mae=0, rmse=0, r2=1):")
    for k, v in compute_all(y_true, y_pred_perfect).items():
        print(f"  {k:5s}: {v:.6f}")

    print("\nMean baseline (expect r2≈0):")
    for k, v in compute_all(y_true, y_pred_baseline).items():
        print(f"  {k:5s}: {v:.6f}")

    print("\nAggregation over 3 fake folds:")
    folds = [
        compute_all(y_true, y_pred_perfect),
        compute_all(y_true, y_pred_baseline),
        compute_all(y_true, y_true + 0.1),
    ]
    agg = aggregate(folds)
    for k, v in agg.items():
        if isinstance(v, dict):
            print(f"  {k:5s}: mean={v['mean']:.4f}  std={v['std']:.4f}")
        else:
            print(f"  {k:5s}: {v}")


if __name__ == "__main__":
    main()