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
    # metrics
    "mae",
    "rmse",
    "r2",
    "compute_all",
    "aggregate",
    "METRIC_NAMES",
    # baseline
    "make_baseline",
    "fit_predict",
    # pipeline
    "run_pipeline",
    "summarize",
    "save_results",
    "build_preprocessor",
]


def __getattr__(name: str):
    """PEP 562 lazy imports.

    Each submodule is loaded only when its symbols are first accessed.
    This keeps `import src.ml` cheap.
    """
    if name in {"run_pipeline", "summarize", "save_results", "build_preprocessor"}:
        from . import pipeline
        return getattr(pipeline, name)
    if name in {"load_features", "build_feature_matrix", "get_feature_names"}:
        from . import data
        return getattr(data, name)

    if name in {"make_loo_cv", "make_kfold_cv", "describe_cv"}:
        from . import split
        return getattr(split, name)

    if name in {"mae", "rmse", "r2", "compute_all", "aggregate", "METRIC_NAMES"}:
        from . import metrics
        return getattr(metrics, name)

    if name in {"make_baseline", "fit_predict"}:
        from . import baseline
        return getattr(baseline, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")