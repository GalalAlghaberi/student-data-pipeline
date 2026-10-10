"""CLI wrapper for src.ml.pipeline.

Usage:
    python scripts/run_ml_pipeline.py
    python scripts/run_ml_pipeline.py --gold-dir data/gold

Reference: docs/ML_EXPERIMENTS.md §8
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Allow running as a plain script: `python scripts/run_ml_pipeline.py`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml import pipeline as ml_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run Phase B ML pipeline (2 CV schemes × 3 models)."
    )
    p.add_argument(
        "--gold-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "gold",
        help="Directory containing ml_features.parquet (default: data/gold).",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    fold_df = ml_pipeline.run_pipeline(gold_dir=args.gold_dir)
    summary_df = ml_pipeline.summarize(fold_df)

    print()
    print("=" * 90)
    print("ML Pipeline — Summary (via scripts/run_ml_pipeline.py)")
    print("=" * 90)
    import pandas as pd
    with pd.option_context(
        "display.max_columns", None,
        "display.width", 240,
        "display.float_format", "{:.4f}".format,
    ):
        print(summary_df.to_string(index=False))

    fold_path, summary_path = ml_pipeline.save_results(
        fold_df, summary_df, gold_dir=args.gold_dir
    )
    print()
    print(f"Saved: {fold_path}")
    print(f"Saved: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())