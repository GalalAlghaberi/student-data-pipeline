"""ML Split Layer — Phase B (Day 1).

Cross-validation strategies for very small N.

Reference: docs/ML_EXPERIMENTS.md §5

Why not train/test split?
  - N=9 → 80/20 would give 7 train + 2 test.
  - Test set of 2 is too noisy for reliable metrics.
  - LOO uses all data (9 folds of 8+1).
  - KFold(3) gives 3 folds of 6+3 for stability comparison.

Both strategies are provided side-by-side for honest reporting.
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
from sklearn.model_selection import KFold, LeaveOneOut

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuration (deterministic)
# ─────────────────────────────────────────────────────────────

RANDOM_STATE: Final = 42
N_SPLITS_KFOLD: Final = 3


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def make_loo_cv() -> LeaveOneOut:
    """Return LeaveOneOut CV splitter (deterministic, no seed needed).

    For N samples, produces N folds of (N-1 train, 1 test).
    """
    return LeaveOneOut()


def make_kfold_cv(
    n_splits: int = N_SPLITS_KFOLD,
    random_state: int = RANDOM_STATE,
) -> KFold:
    """Return KFold CV splitter with shuffle and fixed seed.

    Args:
        n_splits: Number of folds (default 3 — see §5).
        random_state: Fixed seed for reproducibility.

    Returns:
        Configured KFold instance.
    """
    return KFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )


def describe_cv(cv, n_samples: int) -> dict:
    """Return summary metadata for logging and tests.

    Args:
        cv: A scikit-learn CV splitter (LeaveOneOut or KFold).
        n_samples: Number of samples to split.

    Returns:
        Dict with type, n_splits, n_samples, train_sizes, test_sizes.
    """
    dummy = np.zeros(n_samples)
    splits = list(cv.split(dummy))
    sizes = [(len(tr), len(te)) for tr, te in splits]

    return {
        "type": type(cv).__name__,
        "n_splits": len(splits),
        "n_samples": n_samples,
        "train_sizes": sorted({s[0] for s in sizes}),
        "test_sizes": sorted({s[1] for s in sizes}),
    }


# ─────────────────────────────────────────────────────────────
# CLI — Sanity check
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """Sanity check: python -m src.ml.split"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from .data import build_feature_matrix, load_features

    df = load_features()
    X, _ = build_feature_matrix(df)

    print()
    print("=" * 60)
    print("ML Split Layer — Sanity Check")
    print("=" * 60)
    print(f"N samples: {len(X)}")
    print()

    for name, cv in [
        ("LeaveOneOut", make_loo_cv()),
        (f"KFold({N_SPLITS_KFOLD})", make_kfold_cv()),
    ]:
        info = describe_cv(cv, n_samples=len(X))
        print(f"{name}:")
        for k, v in info.items():
            print(f"  {k:14s}: {v}")
        print()


if __name__ == "__main__":
    main()