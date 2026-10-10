"""ML Metrics Layer — Phase B (Day 1).

MAE / RMSE / R² computed uniformly across CV folds.

Reference: docs/ML_EXPERIMENTS.md §7

Why three metrics?
  - MAE:  intuitive (GPA points, same unit as target).
  - RMSE: penalizes large errors (sensitive to outliers).
  - R²:   normalized against the mean baseline.

Edge case — R² on LOO:
  LeaveOneOut folds have n_test = 1. R² is undefined for a single
  sample (SS_tot = 0 → division by zero). We return NaN silently
  instead of letting sklearn emit UndefinedMetricWarning on every
  fold. `aggregate()` excludes NaN and reports `n_valid` so callers
  know how many folds actually contributed to r2_mean / r2_std.
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
    """R² score (unitless). Returns NaN when n < 2 (undefined).

    LOO folds have n_test=1 → R² is undefined. We return NaN silently
    to avoid sklearn's UndefinedMetricWarning spam.
    """
    y_true = np.asarray(y_true).ravel()
    if y_true.size < 2:
        return float("nan")
    return float(r2_score(y_true, y_pred))


def compute_all(y_true, y_pred) -> dict[str, float]:
    """Return {mae, rmse, r2} for one fold."""
    return {
        "mae":  mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "r2":   r2(y_true, y_pred),
    }


# ─────────────────────────────────────────────────────────────
# Aggregation across CV folds
# ─────────────────────────────────────────────────────────────

def aggregate(fold_metrics: list[dict[str, float]]) -> dict[str, dict]:
    """Aggregate fold metric dicts into {metric: {mean, std, n_valid}}.

    NaN values (e.g., R² on LOO's single-sample folds) are excluded
    from mean/std and reported via `n_valid`.

    Args:
        fold_metrics: One dict per fold (output of `compute_all`).

    Returns:
        {
          "mae":  {"mean": ..., "std": ..., "n_valid": N},
          "rmse": {"mean": ..., "std": ..., "n_valid": N},
          "r2":   {"mean": ..., "std": ..., "n_valid": N},
          "n_folds": int,
        }
        When n_valid == 0 for a metric, mean/std are NaN.
    """
    if not fold_metrics:
        raise ValueError("fold_metrics is empty")

    out: dict[str, dict] = {}
    for name in METRIC_NAMES:
        values = np.array([fm[name] for fm in fold_metrics], dtype=float)
        valid = ~np.isnan(values)
        n_valid = int(valid.sum())
        if n_valid == 0:
            out[name] = {
                "mean": float("nan"),
                "std":  float("nan"),
                "n_valid": 0,
            }
        else:
            out[name] = {
                "mean": float(values[valid].mean()),
                "std":  float(values[valid].std(ddof=1)) if n_valid > 1 else 0.0,
                "n_valid": n_valid,
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

    print("\nMean baseline (expect r2=0):")
    for k, v in compute_all(y_true, y_pred_baseline).items():
        print(f"  {k:5s}: {v:.6f}")

    print("\nSingle-sample fold (expect r2=NaN):")
    for k, v in compute_all(y_true[:1], y_pred_baseline[:1]).items():
        print(f"  {k:5s}: {v}")

    print("\nAggregation over 3 fake folds:")
    folds = [
        compute_all(y_true, y_pred_perfect),
        compute_all(y_true, y_pred_baseline),
        compute_all(y_true, y_true + 0.1),
    ]
    agg = aggregate(folds)
    for k, v in agg.items():
        if isinstance(v, dict):
            print(
                f"  {k:5s}: mean={v['mean']:.4f}  "
                f"std={v['std']:.4f}  n_valid={v['n_valid']}"
            )
        else:
            print(f"  {k:5s}: {v}")

    print("\nAggregation with NaN (2 folds, 1 has r2=NaN):")
    folds_nan = [
        compute_all(y_true, y_pred_perfect),
        compute_all(y_true[:1], y_pred_perfect[:1]),   # ← r2 = NaN
    ]
    agg_nan = aggregate(folds_nan)
    for k, v in agg_nan.items():
        if isinstance(v, dict):
            print(
                f"  {k:5s}: mean={v['mean']:.4f}  "
                f"std={v['std']:.4f}  n_valid={v['n_valid']}"
            )
        else:
            print(f"  {k:5s}: {v}")


if __name__ == "__main__":
    main()