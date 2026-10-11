"""CLI wrapper for the Phase B.7 ML pipeline (v2).

Usage:
    python scripts/run_ml_pipeline_v2.py
    python scripts/run_ml_pipeline_v2.py --fs A
    python scripts/run_ml_pipeline_v2.py --cv group_kfold_5 group_kfold_3
    python scripts/run_ml_pipeline_v2.py --log-level DEBUG

Runs the full CV × model × feature-set matrix documented in
docs/ML_EXPERIMENTS_SCALE.md §4-6, then writes:
  data/gold/model_metrics_v2.csv        (per-fold raw)
  data/gold/model_metrics_v2.json       (summary, mean ± std)
  data/gold/feature_importance_v2.csv   (RF + GBM per fold)

Reference: docs/ML_EXPERIMENTS_SCALE.md §9 (file plan)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

# Ensure project root is on sys.path when running this file directly.
# Without this, `python scripts/run_ml_pipeline_v2.py` sets sys.path[0]
# to the scripts/ directory, and `from src.ml import ...` fails with
# ModuleNotFoundError. Under pytest this is a no-op.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.pipeline_v2 import (  # noqa: E402
    CV_SCHEMES,
    FEATURE_SETS,
    GOLD_DIR,
    run_pipeline_v2,
    save_results_v2,
    summarize_v2,
)

logger = logging.getLogger("run_ml_pipeline_v2")


# ═══════════════════════════════════════════════════════════════
# Argument parsing
# ═══════════════════════════════════════════════════════════════

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        argv: Optional argv override (used by tests).

    Returns:
        argparse.Namespace with `gold_dir`, `fs`, `cv`, `log_level`.
    """
    parser = argparse.ArgumentParser(
        prog="run_ml_pipeline_v2",
        description="Phase B.7 ML Scale-Up pipeline (UCI-only, N=1,044).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/run_ml_pipeline_v2.py\n"
            "  python scripts/run_ml_pipeline_v2.py --fs A --cv group_kfold_5\n"
            "  python scripts/run_ml_pipeline_v2.py --log-level DEBUG\n"
        ),
    )
    parser.add_argument(
        "--gold-dir", type=Path, default=GOLD_DIR,
        help=f"Destination for outputs (default: {GOLD_DIR})",
    )
    parser.add_argument(
        "--fs", nargs="+", choices=list(FEATURE_SETS), default=list(FEATURE_SETS),
        help=f"Feature sets to run (default: {list(FEATURE_SETS)})",
    )
    parser.add_argument(
        "--cv", nargs="+", choices=list(CV_SCHEMES), default=list(CV_SCHEMES),
        help=f"CV schemes to run (default: {list(CV_SCHEMES)})",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    return parser.parse_args(argv)


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    """Run the full v2 pipeline and print a summary table.

    Returns:
        Exit code: 0 on success, 1 on unexpected error.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    logger.info(
        "Starting B.7.6 pipeline: fs=%s cv=%s",
        args.fs, args.cv,
    )
    t0 = time.perf_counter()

    try:
        fold_df, importance_df = run_pipeline_v2(
            gold_dir=args.gold_dir,
            feature_sets=tuple(args.fs),
            cv_schemes=tuple(args.cv),
        )
        summary_df = summarize_v2(fold_df)

        print()
        print("=" * 110)
        print("ML Pipeline v2 — Summary")
        print("=" * 110)
        print(f"Feature sets:   {args.fs}")
        print(f"CV schemes:     {args.cv}")
        print(f"Fold rows:      {len(fold_df):,}")
        print(f"Summary cells:  {len(summary_df)}")
        print(f"Importance:     {len(importance_df):,} rows")
        print()

        with pd.option_context(
            "display.max_columns", None,
            "display.width", 240,
            "display.float_format", "{:.4f}".format,
        ):
            print(summary_df.to_string(index=False))

        fold_path, summary_path, importance_path = save_results_v2(
            fold_df, summary_df, importance_df, gold_dir=args.gold_dir,
        )

        elapsed = time.perf_counter() - t0
        print()
        print(f"Saved fold CSV:       {fold_path}")
        print(f"Saved summary JSON:   {summary_path}")
        print(f"Saved importance CSV: {importance_path}")
        print(f"Total elapsed:        {elapsed:.1f}s")
        print()
        return 0

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.", file=sys.stderr)
        return 130

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        print(f"\n[X] Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())