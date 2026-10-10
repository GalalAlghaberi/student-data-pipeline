"""ML Pipeline — Phase B (Day 1).

End-to-end orchestrator:
  1. Load features (leakage-safe).
  2. Encode categoricals (OneHotEncoder) + passthrough numerics.
  3. Run 2 CV schemes (LOO, KFold-3) × 3 models (baseline, linear, ridge).
  4. Aggregate metrics.
  5. Persist results to data/gold/.

Reference: docs/ML_EXPERIMENTS.md §5-7

Notes on R²:
  - LOO folds have n_test=1 → R² is mathematically undefined.
    metrics.r2() returns NaN; metrics.aggregate() excludes NaN and
    reports `n_valid` so downstream code knows how many folds
    contributed to r2_mean / r2_std.
  - KFold(3) folds have n_test=3 → R² is defined but may be very
    negative with so few samples (small SS_tot). Documented in §7.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from . import data as data_mod
from . import metrics as metrics_mod
from . import split as split_mod
from . import trainer as trainer_mod

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent.parent
GOLD_DIR: Final = PROJECT_ROOT / "data" / "gold"

OUTPUT_CSV: Final = "model_metrics.csv"
OUTPUT_JSON: Final = "model_metrics.json"

# CV schemes to run (name → factory)
CV_SCHEMES: Final[dict] = {
    "loo":    split_mod.make_loo_cv,
    "kfold3": split_mod.make_kfold_cv,
}

# Models to run (name → fit_predict callable)
# Note: baseline is handled specially in `_run_fold` because it ignores
# X entirely and predicts the training mean.
MODELS: Final[dict] = {
    "baseline": None,          # handled specially (see _run_fold)
    "linear":   trainer_mod.fit_predict_linear,
    "ridge":    trainer_mod.fit_predict_ridge,
}


# ─────────────────────────────────────────────────────────────
# Preprocessing — encode categoricals
# ─────────────────────────────────────────────────────────────

def build_preprocessor() -> ColumnTransformer:
    """Return ColumnTransformer: OneHot on categoricals, passthrough numerics.

    Why OneHotEncoder(handle_unknown='ignore'):
      - LOO may leave a category unseen in a fold.
      - KFold(3) may leave 'city=Dhamar' fully in test fold.
      - handle_unknown='ignore' prevents crashes; unknown → all zeros.
    """
    return ColumnTransformer(
        transformers=[
            ("num", "passthrough", data_mod.FEATURES_NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             data_mod.FEATURES_CATEGORICAL),
        ],
        remainder="drop",
    )


# ─────────────────────────────────────────────────────────────
# Single-fold execution
# ─────────────────────────────────────────────────────────────

def _run_fold(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    """Run one CV fold for one model, return metrics dict.

    The preprocessor is fit on X_train only (leakage-safe) and reused
    for X_test via .transform().
    """
    if model_name == "baseline":
        # Baseline ignores X entirely (predicts mean of y_train).
        # FIX: use module-level `np`, not `trainer_mod.np`.
        preds = np.full_like(
            np.asarray(y_test, dtype=float),
            float(np.mean(y_train)),
        )
    else:
        fn = MODELS[model_name]
        pre = build_preprocessor()
        X_train_t = pre.fit_transform(X_train)
        X_test_t = pre.transform(X_test)
        preds = fn(X_train_t, y_train, X_test_t)

    return metrics_mod.compute_all(y_test, preds)


# ─────────────────────────────────────────────────────────────
# Main orchestration
# ─────────────────────────────────────────────────────────────

def run_pipeline(gold_dir: Path = GOLD_DIR) -> pd.DataFrame:
    """Run all (CV scheme × model) combinations, return long-form DataFrame.

    Args:
        gold_dir: Where ml_features.parquet lives (and where outputs go).

    Returns:
        DataFrame with columns:
          cv, model, fold, mae, rmse, r2
        (r2 may be NaN for LOO folds where n_test=1.)
    """
    df = data_mod.load_features(gold_dir)
    X, y = data_mod.build_feature_matrix(df)

    rows: list[dict] = []
    for cv_name, cv_factory in CV_SCHEMES.items():
        cv = cv_factory()
        for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
            X_train = X.iloc[train_idx]
            y_train = y.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_test = y.iloc[test_idx]

            for model_name in MODELS:
                m = _run_fold(model_name, X_train, y_train, X_test, y_test)
                rows.append({
                    "cv": cv_name,
                    "model": model_name,
                    "fold": fold_idx,
                    **m,
                })
            logger.debug(
                "cv=%s fold=%d done (n_train=%d, n_test=%d)",
                cv_name, fold_idx, len(train_idx), len(test_idx),
            )

    return pd.DataFrame(rows)


def summarize(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-fold metrics → mean ± std per (cv, model).

    Returns a wide DataFrame with columns:
      cv, model, n_folds,
      mae_mean, mae_std, rmse_mean, rmse_std,
      r2_mean, r2_std, r2_n_valid

    `r2_n_valid` = number of folds where R² was defined (n_test ≥ 2).
      - LOO    → r2_n_valid = 0   (all folds have n_test=1)
      - KFold3 → r2_n_valid = 3   (all folds have n_test=3)
    """
    agg_rows = []
    for (cv_name, model_name), group in fold_df.groupby(["cv", "model"]):
        agg = metrics_mod.aggregate(group.to_dict("records"))
        agg_rows.append({
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
        .sort_values(["cv", "model"])
        .reset_index(drop=True)
    )


# ─────────────────────────────────────────────────────────────
# Persistence
# ─────────────────────────────────────────────────────────────

def save_results(
    fold_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    gold_dir: Path = GOLD_DIR,
) -> tuple[Path, Path]:
    """Save per-fold (CSV) and summary (JSON) to gold_dir.

    Returns:
        (fold_csv_path, summary_json_path)
    """
    gold_dir.mkdir(parents=True, exist_ok=True)

    fold_path = gold_dir / OUTPUT_CSV
    summary_path = gold_dir / OUTPUT_JSON

    # Save per-fold CSV (raw)
    fold_df.to_csv(fold_path, index=False, float_format="%.6f")
    logger.info("Wrote %s (%d rows)", fold_path, len(fold_df))

    # Save summary JSON (nested). NaN → null in JSON.
    summary_json = {
        "generated_by": "src.ml.pipeline",
        "n_rows": int(len(summary_df)),
        "results": summary_df.to_dict(orient="records"),
    }
    summary_path.write_text(
        json.dumps(summary_json, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote %s", summary_path)

    return fold_path, summary_path


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main() -> None:
    """Run pipeline: python -m src.ml.pipeline"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    fold_df = run_pipeline()
    summary_df = summarize(fold_df)

    print()
    print("=" * 90)
    print("ML Pipeline — Summary (mean ± std across folds)")
    print("=" * 90)
    with pd.option_context(
        "display.max_columns", None,
        "display.width", 240,
        "display.float_format", "{:.4f}".format,
    ):
        print(summary_df.to_string(index=False))

    fold_path, summary_path = save_results(fold_df, summary_df)
    print()
    print(f"Saved: {fold_path}")
    print(f"Saved: {summary_path}")


if __name__ == "__main__":
    main()