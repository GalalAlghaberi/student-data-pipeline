"""ML Split Layer v2 — Phase B.7 (Scale-Up).

Cross-validation strategies for N=1,044 (662 unique students).

Reference: docs/ML_EXPERIMENTS_SCALE.md §5

Four schemes (declared in §5.5):
  1. GroupKFold(5)  — PRIMARY, enforces student-level isolation
  2. KFold(5)       — secondary, quantifies the leak
  3. LeaveOneOut    — tertiary, v1 bridge (comparability only)
  4. GroupKFold(3)  — quaternary, stability check

Key invariant:
  In GroupKFold, no `student_id` (group) may appear in both train and
  test of the same fold. Enforced by `assert_no_group_leakage()`.

Why not plain KFold?
  The Silver dataset has 662 unique students across 1,044 rows.
  A naive KFold(shuffle=True) can place the same student's math row in
  train and portuguese row in test. Because those rows share nearly
  identical age / gender / city / attendance, the model appears to
  generalize while memorizing student identity.

Golden Rules:
  - Add a layer; do not replace (v1 split.py stays intact).
  - Deterministic (random_state=42 for KFold shuffle).
  - No changes to src/ml/split.py (v1).
"""

from __future__ import annotations

import logging
from typing import Final

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold, LeaveOneOut

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration (deterministic)
# ═══════════════════════════════════════════════════════════════

RANDOM_STATE: Final = 42
N_SPLITS_PRIMARY: Final = 5
N_SPLITS_STABILITY: Final = 3


# ═══════════════════════════════════════════════════════════════
# CV factories
# ═══════════════════════════════════════════════════════════════

def make_group_kfold_5() -> GroupKFold:
    """Return GroupKFold(5) — the primary scheme (docs §5.1).

    Groups (student_id) must be passed to `.split(X, y, groups=...)`.
    """
    return GroupKFold(n_splits=N_SPLITS_PRIMARY)


def make_group_kfold_3() -> GroupKFold:
    """Return GroupKFold(3) — stability check (docs §5.4)."""
    return GroupKFold(n_splits=N_SPLITS_STABILITY)


def make_kfold_5(
    random_state: int = RANDOM_STATE,
) -> KFold:
    """Return KFold(5, shuffle=True) — leak demonstration (docs §5.2).

    This scheme intentionally ignores groups. Comparing its metrics to
    GroupKFold(5) shows how much optimism the naive split introduces.
    """
    return KFold(
        n_splits=N_SPLITS_PRIMARY,
        shuffle=True,
        random_state=random_state,
    )


def make_loo() -> LeaveOneOut:
    """Return LeaveOneOut — v1 bridge for comparability (docs §5.3).

    With N=1,044, this yields 1,044 folds. R² is NaN per fold
    (n_test=1) — handled by metrics.r2() in v1 (unchanged).
    """
    return LeaveOneOut()


# ═══════════════════════════════════════════════════════════════
# Leakage verification (THE critical invariant)
# ═══════════════════════════════════════════════════════════════

def assert_no_group_leakage(
    cv,
    X,
    y,
    groups,
) -> dict:
    """Verify no group appears in both train and test of any fold.

    This is the single most important correctness check in B.7. Called
    by tests AND by pipeline_v2 before running any group-aware CV.

    Args:
        cv:     CV splitter (GroupKFold recommended).
        X:      Features (only used for its length).
        y:      Target (only used for its shape).
        groups: Array-like of group ids (e.g., student_id).

    Returns:
        Dict with:
            n_folds:          number of folds
            fold_stats:       list of dicts (one per fold)
                              each: fold, n_train, n_test,
                                    n_train_groups, n_test_groups

    Raises:
        AssertionError: If any group overlaps between train and test.
    """
    groups_arr = np.asarray(groups)
    fold_stats: list[dict] = []

    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y, groups=groups_arr)):
        train_groups = set(groups_arr[train_idx].tolist())
        test_groups = set(groups_arr[test_idx].tolist())
        overlap = train_groups & test_groups

        assert not overlap, (
            f"Group leakage in fold {fold_idx}: "
            f"{len(overlap)} group(s) appear in both train and test. "
            f"Examples: {sorted(overlap)[:3]}"
        )

        fold_stats.append({
            "fold":            fold_idx,
            "n_train":         int(len(train_idx)),
            "n_test":          int(len(test_idx)),
            "n_train_groups":  int(len(train_groups)),
            "n_test_groups":   int(len(test_groups)),
        })

    logger.info(
        "Group leakage check passed for %s (%d folds)",
        type(cv).__name__, len(fold_stats),
    )
    return {
        "n_folds":    len(fold_stats),
        "fold_stats": fold_stats,
    }


# ═══════════════════════════════════════════════════════════════
# Metadata for logging and tests
# ═══════════════════════════════════════════════════════════════

def describe_cv(cv, n_samples: int, groups=None) -> dict:
    """Return summary metadata for logging and tests.

    Note: train_sizes and test_sizes are UNIQUE sizes (a sorted set),
    not per-fold sizes. For GroupKFold(5) on 1,044 rows, test_sizes
    will be [208, 209] — two unique values, not five entries.

    Args:
        cv:        CV splitter.
        n_samples: Number of samples to split.
        groups:    Optional group array (required by GroupKFold).

    Returns:
        Dict with type, n_splits, n_samples, train_sizes, test_sizes.
    """
    dummy_X = np.zeros(n_samples)
    dummy_y = np.zeros(n_samples)

    if groups is None:
        splits = list(cv.split(dummy_X, dummy_y))
    else:
        groups_arr = np.asarray(groups)
        splits = list(cv.split(dummy_X, dummy_y, groups=groups_arr))

    train_sizes = sorted({len(tr) for tr, _ in splits})
    test_sizes = sorted({len(te) for _, te in splits})

    return {
        "type":        type(cv).__name__,
        "n_splits":    len(splits),
        "n_samples":   n_samples,
        "train_sizes": train_sizes,
        "test_sizes":  test_sizes,
    }


# ═══════════════════════════════════════════════════════════════
# Registry (used by pipeline_v2)
# ═══════════════════════════════════════════════════════════════

CV_SCHEMES: Final[dict[str, callable]] = {
    "group_kfold_5": make_group_kfold_5,
    "kfold_5":       make_kfold_5,
    "loo":           make_loo,
    "group_kfold_3": make_group_kfold_3,
}

# Schemes that accept `groups=` in `.split()`
GROUP_AWARE_SCHEMES: Final[frozenset] = frozenset({
    "group_kfold_5", "group_kfold_3",
})


# ═══════════════════════════════════════════════════════════════
# CLI — Sanity check
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Sanity check: python -m src.ml.split_v2"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    from .data_v2 import build_feature_matrix_v2, load_uci_only

    df = load_uci_only()
    X, y, groups = build_feature_matrix_v2(df, fs="A")

    print()
    print("=" * 70)
    print("ML Split Layer v2 — Sanity Check")
    print("=" * 70)
    print(f"N samples:      {len(X):,}")
    print(f"Unique groups:  {groups.nunique():,}")
    print()

    for name, factory in CV_SCHEMES.items():
        cv = factory()
        info = describe_cv(cv, n_samples=len(X), groups=groups)
        print(f"[{name}]")
        print(f"  type:        {info['type']}")
        print(f"  n_splits:    {info['n_splits']}")
        print(f"  train_sizes: {info['train_sizes']}")
        print(f"  test_sizes:  {info['test_sizes']}")

        if name in GROUP_AWARE_SCHEMES:
            stats = assert_no_group_leakage(cv, X, y, groups)
            print(f"  leakage:     [OK] PASS ({stats['n_folds']} folds)")
        print()

    print("Registry entries:")
    for name in CV_SCHEMES:
        marker = "[G] group-aware" if name in GROUP_AWARE_SCHEMES else "[R] row-aware"
        print(f"  {name:16s} {marker}")


if __name__ == "__main__":
    main()