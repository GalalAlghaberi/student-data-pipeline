"""ML Layer — Phase B (Day 1).

Reference: docs/ML_EXPERIMENTS.md
"""
from __future__ import annotations

__all__ = [
    # data
    "load_features",
    "build_feature_matrix",
    "get_feature_names",
    # split
    "make_loo_cv",
    "make_kfold_cv",
    "describe_cv",
]


def __getattr__(name: str):
    """PEP 562 lazy imports."""
    if name in {"load_features", "build_feature_matrix", "get_feature_names"}:
        from . import data
        return getattr(data, name)
    if name in {"make_loo_cv", "make_kfold_cv", "describe_cv"}:
        from . import split
        return getattr(split, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")