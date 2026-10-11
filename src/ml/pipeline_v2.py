"""ML Pipeline v2 — Phase B.7 (Scale-Up).

End-to-end orchestrator for the scale-up experiments:
  1. Load UCI-only Silver (1,044 rows, 662 students)
  2. For each FS in {A, B}:
     For each CV scheme in {GroupKFold5, KFold5, GroupKFold3, LOO}:
       For each fold:
         - Fit OneHotEncoder on X_train (per-fold, leakage-safe)
         - Fit 5 models: baseline, linear, ridge, rf, gbm
         - Collect per-fold metrics
  3. Persist:
     - model_metrics_v2.csv    — per-fold raw
     - model_metrics_v2.json   — summary (mean ± std per cell)
     - feature_importance_v2.csv — RF + GBM per fold

Reference: docs/ML_EXPERIMENTS_SCALE.md §4, §5, §6, §9

Design note (LOO cost):
  LOO yields 1,044 folds. RF/GBM at ~0.5-1s/fit would need ~26 min
  per FS. LOO is therefore restricted to {baseline, linear, ridge} —
  the same models v1 used. GroupKFold(5) is the primary scheme for
  tree models.

40-cell experiment matrix (CV × model × FS):
  GroupKFold5    × 5 models × 2 FS = 10 cells
  KFold5         × 5 models × 2 FS = 10 cells
  GroupKFold3    × 5 models × 2 FS = 10 cells
  LOO            × 3 models × 2 FS =  6 cells  (baseline/linear/ridge only)
  ─────────────────────────────────────────────
  Total: 36 cells  (LOO adds 6, not 10)

CSV row count:
  GroupKFold5    × 5 folds × 5 models × 2 FS =    50 rows
  KFold5         × 5 folds × 5 models × 2 FS =    50 rows
  GroupKFold3    × 3 folds × 5 models × 2 FS =    30 rows
  LOO            × 1,044 folds × 3 models × 2 FS = 6,264 rows
  ──────────────────────────────────────────────────────────
  Total:                                          6,394 rows

Golden Rules:
  - Add a layer; do not replace (v1 pipeline.py stays FROZEN).
  - No changes to src/ml/data.py, split.py, trainer.py, metrics.py.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.preprocessing import OneHotEncoder

from . import data_v2 as data_mod
from . import metrics as metrics_mod
from . import split_v2 as split_mod
from . import trainer_v2 as trainer_mod

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent.parent
GOLD_DIR: Final = PROJECT_ROOT / "data" / "gold"

OUTPUT_FOLD_CSV: Final = "model_metrics_v2.csv"
OUTPUT_SUMMARY_JSON: Final = "model_metrics_v2.json"
OUTPUT_IMPORTANCE_CSV: Final = "feature_importance_v2.csv"

# All 4 CV schemes (from split_v2)
CV_SCHEMES: Final[tuple[str, ...]] = (
    "group_kfold_5",
    "kfold_5",
    "group_kfold_3",
    "loo",
)

# All 5 models (baseline handled specially — ignores X)
ALL_MODELS: Final[tuple[str, ...]] = ("baseline", "linear", "ridge", "rf", "gbm")

# LOO restricted to models v1 used (see module docstring)
LOO_MODELS: Final[frozenset] = frozenset({"baseline", "linear", "ridge"})

# Feature sets to evaluate
FEATURE_SETS: Final[tuple[str, ...]] = ("A", "B")


# ═══════════════════════════════════════════════════════════════
# Preprocessing — per-fold OneHotEncoder
# ═══════════════════════════════════════════════════════════════

def build_preprocessor(fs: str) -> ColumnTransformer:
    """Return ColumnTransformer: OneHot on categoricals, passthrough numerics.

    Configuration (docs/ML_EXPERIMENTS_SCALE.md §4.4):
        handle_unknown="ignore"  — safety against unseen categories
        drop="first"             — avoids dummy-variable trap
        sparse_output=False      — dense output (RF/GBM work fine)

    Args:
        fs: "A" or "B" — selects which numeric/categorical columns.

    Returns:
        Unfitted ColumnTransformer.
    """
    numeric, categorical = data_mod._fs_columns(fs)
    return ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric),
            ("cat", OneHotEncoder(
                handle_unknown="ignore",
                drop="first",
                sparse_output=False,
            ), categorical),
        ],
        remainder="drop",
    )


# ═══════════════════════════════════════════════════════════════
# Single-fold execution
# ═══════════════════════════════════════════════════════════════

def _run_fold(
    model_name: str,
    fs: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> tuple[dict[str, float], dict[str, float] | None]:
    """Run one CV fold for one model. Return (metrics, feature_importance).

    feature_importance is None unless model is rf or gbm.
    """
    if model_name == "baseline":
        # Baseline ignores X entirely
        preds = np.full_like(
            np.asarray(y_test, dtype=float),
            float(np.mean(y_train)),
        )
        return metrics_mod.compute_all(y_test, preds), None

    # Build + fit preprocessor on train only
    pre = build_preprocessor(fs)
    X_train_t = pre.fit_transform(X_train)
    X_test_t = pre.transform(X_test)

    # Fit + predict
    fn = trainer_mod.get_trainer_v2(model_name)
    preds = fn(X_train_t, y_train, X_test_t)

    metrics = metrics_mod.compute_all(y_test, preds)

    # Feature importance (rf/gbm only)
    importance = None
    if model_name in ("rf", "gbm"):
        model = (
            trainer_mod.make_random_forest()
            if model_name == "rf"
            else trainer_mod.make_gradient_boosting()
        )
        model.fit(X_train_t, y_train)
        feature_names = list(pre.get_feature_names_out())
        importance = trainer_mod.extract_feature_importance(model, feature_names)

    return metrics, importance


# ═══════════════════════════════════════════════════════════════
# Main orchestration
# ═══════════════════════════════════════════════════════════════

def run_pipeline_v2(
    gold_dir: Path = GOLD_DIR,
    feature_sets: tuple[str, ...] = FEATURE_SETS,
    cv_schemes: tuple[str, ...] = CV_SCHEMES,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the full B.7 experiment matrix.

    Args:
        gold_dir:     Directory containing ml_features.parquet (used by v1
                      metrics module) and destination for output files.
        feature_sets: Subset of {"A", "B"} to run.
        cv_schemes:   Subset of CV_SCHEMES to run.

    Returns:
        (fold_df, importance_df)
        fold_df:       one row per (fs, cv, model, fold)
        importance_df: one row per (fs, cv, model, fold, feature)
    """
    df_uci = data_mod.load_uci_only()
    logger.info(
        "Loaded UCI-only: %d rows, %d students",
        len(df_uci), df_uci["student_id"].nunique(),
    )

    fold_rows: list[dict] = []
    importance_rows: list[dict] = []

    t_start = time.perf_counter()

    for fs in feature_sets:
        X, y, groups = data_mod.build_feature_matrix_v2(df_uci, fs=fs)

        for cv_name in cv_schemes:
            cv = split_mod.CV_SCHEMES[cv_name]()
            is_group_aware = cv_name in split_mod.GROUP_AWARE_SCHEMES
            is_loo = cv_name == "loo"

            # LOO restriction — see module docstring
            models_to_run = ALL_MODELS if not is_loo else tuple(
                m for m in ALL_MODELS if m in LOO_MODELS
            )

            if is_group_aware:
                split_iter = cv.split(X, y, groups=groups)
            else:
                split_iter = cv.split(X, y)

            for fold_idx, (train_idx, test_idx) in enumerate(split_iter):
                X_train = X.iloc[train_idx]
                y_train = y.iloc[train_idx]
                X_test = X.iloc[test_idx]
                y_test = y.iloc[test_idx]

                for model_name in models_to_run:
                    metrics, importance = _run_fold(
                        model_name, fs,
                        X_train, y_train, X_test, y_test,
                    )
                    fold_rows.append({
                        "fs":    fs,
                        "cv":    cv_name,
                        "model": model_name,
                        "fold":  fold_idx,
                        **metrics,
                    })
                    if importance is not None:
                        for feat, imp in importance.items():
                            importance_rows.append({
                                "fs":        fs,
                                "cv":        cv_name,
                                "model":     model_name,
                                "fold":      fold_idx,
                                "feature":   feat,
                                "importance": imp,
                            })

            logger.info(
                "Done fs=%s cv=%s (%d folds, %d models)",
                fs, cv_name, fold_idx + 1, len(models_to_run),
            )

    elapsed = time.perf_counter() - t_start
    logger.info(
        "Full matrix complete: %d fold-rows, %d importance-rows, %.1fs",
        len(fold_rows), len(importance_rows), elapsed,
    )

    return (
        pd.DataFrame(fold_rows),
        pd.DataFrame(importance_rows),
    )


# ═══════════════════════════════════════════════════════════════
# Summarization
# ═══════════════════════════════════════════════════════════════

def summarize_v2(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-fold metrics → mean ± std per (fs, cv, model).

    Returns wide DataFrame:
        fs, cv, model, n_folds,
        mae_mean, mae_std, rmse_mean, rmse_std,
        r2_mean, r2_std, r2_n_valid
    """
    agg_rows = []
    for (fs, cv_name, model_name), group in fold_df.groupby(
        ["fs", "cv", "model"], sort=False,
    ):
        agg = metrics_mod.aggregate(group.to_dict("records"))
        agg_rows.append({
            "fs":         fs,
            "cv":         cv_name,
            "model":      model_name,
            "n_folds":    agg["n_folds"],
            "mae_mean":   agg["mae"]["mean"],
            "mae_std":    agg["mae"]["std"],
            "rmse_mean":  agg["rmse"]["mean"],
            "rmse_std":   agg["rmse"]["std"],
            "r2_mean":    agg["r2"]["mean"],
            "r2_std":     agg["r2"]["std"],
            "r2_n_valid": agg["r2"]["n_valid"],
        })
    return (
        pd.DataFrame(agg_rows)
        .sort_values(["fs", "cv", "model"])
        .reset_index(drop=True)
    )


# ═══════════════════════════════════════════════════════════════
# Persistence
# ═══════════════════════════════════════════════════════════════

def save_results_v2(
    fold_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    importance_df: pd.DataFrame,
    gold_dir: Path = GOLD_DIR,
) -> tuple[Path, Path, Path]:
    """Save per-fold CSV, summary JSON, and feature-importance CSV.

    Returns:
        (fold_csv_path, summary_json_path, importance_csv_path)
    """
    gold_dir.mkdir(parents=True, exist_ok=True)

    fold_path = gold_dir / OUTPUT_FOLD_CSV
    summary_path = gold_dir / OUTPUT_SUMMARY_JSON
    importance_path = gold_dir / OUTPUT_IMPORTANCE_CSV

    fold_df.to_csv(fold_path, index=False, float_format="%.6f")
    logger.info("Wrote %s (%d rows)", fold_path, len(fold_df))

    summary_json = {
        "generated_by":   "src.ml.pipeline_v2",
        "n_cells":        int(len(summary_df)),
        "n_fold_rows":    int(len(fold_df)),
        "n_importance":   int(len(importance_df)),
        "results":        summary_df.to_dict(orient="records"),
    }
    summary_path.write_text(
        json.dumps(summary_json, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote %s", summary_path)

    if not importance_df.empty:
        importance_df.to_csv(importance_path, index=False, float_format="%.6f")
        logger.info("Wrote %s (%d rows)", importance_path, len(importance_df))

    return fold_path, summary_path, importance_path


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Run full pipeline: python -m src.ml.pipeline_v2"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    fold_df, importance_df = run_pipeline_v2()
    summary_df = summarize_v2(fold_df)

    print()
    print("=" * 110)
    print("ML Pipeline v2 — Summary (mean ± std across folds)")
    print("=" * 110)
    with pd.option_context(
        "display.max_columns", None,
        "display.width", 240,
        "display.float_format", "{:.4f}".format,
    ):
        print(summary_df.to_string(index=False))

    fold_path, summary_path, importance_path = save_results_v2(
        fold_df, summary_df, importance_df,
    )

    print()
    print(f"Fold CSV:          {fold_path}  ({len(fold_df):,} rows)")
    print(f"Summary JSON:      {summary_path}  ({len(summary_df)} cells)")
    print(f"Importance CSV:    {importance_path}  ({len(importance_df):,} rows)")
    print()


if __name__ == "__main__":
    main()