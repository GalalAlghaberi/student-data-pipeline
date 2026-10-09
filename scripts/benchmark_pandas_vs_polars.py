"""Benchmark: Pandas vs Polars on identical synthetic data.

Methodology (documented BEFORE execution — Golden Rule 4):
  - Sizes: 100K, 1M
  - Warm-up: 1 run (discarded)
  - Measured runs: 5 → median
  - Operation: row-wise derived features (post-aggregation)
  - Metrics: wall time (ms) + peak memory (MB, tracemalloc)
  - Same data for both engines (fair comparison)

Reference:
  - docs/POLARS_MIGRATION.md §8 (Benchmark Methodology)
  - Unit 6 (p. 60, Scalability Wall)
  - Guide Ch 5 (Compute & Resources)

Honesty clause:
  Results are ENVIRONMENT-SPECIFIC (Windows 11, Python 3.14.7,
  Polars 1.44.2). They do NOT generalize. They demonstrate that
  both engines work correctly and show the Lazy advantage.
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import polars as pl

# Ensure `src.*` is importable when running as `python scripts/...`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.synthetic_generator import generate_synthetic  # noqa: E402


logger = logging.getLogger("benchmark")


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

DEFAULT_SEED = 42
WARMUP_RUNS = 1
MEASURED_RUNS = 5
DEFAULT_SIZES = [100_000, 1_000_000]


# ═══════════════════════════════════════════════════════════════
# Operations (mirror engineering.py post-aggregation step)
# ═══════════════════════════════════════════════════════════════

def _pandas_feature_ops(df: pd.DataFrame) -> pd.DataFrame:
    """Mirror row-wise derived features from engineering.py."""
    df = df.copy()
    df["attendance_rate"] = (df["attendance"] / 100.0).round(4)
    df["academic_risk_score"] = (
        (4.0 - df["gpa"]) + ((100.0 - df["attendance"]) / 25.0)
    ).round(4)
    df["performance_level"] = np.select(
        [
            df["gpa"] >= 3.5,
            df["gpa"] >= 3.0,
            df["gpa"] >= 2.5,
            df["gpa"] >= 2.0,
        ],
        ["Excellent", "Very Good", "Good", "Pass"],
        default="Weak",
    )
    return df


def _polars_feature_ops(df: pl.DataFrame) -> pl.DataFrame:
    """Same operations — Polars eager mode."""
    return df.with_columns([
        (pl.col("attendance") / 100.0).round(4).alias("attendance_rate"),
        (
            (4.0 - pl.col("gpa"))
            + ((100.0 - pl.col("attendance")) / 25.0)
        ).round(4).alias("academic_risk_score"),
        pl.when(pl.col("gpa") >= 3.5).then(pl.lit("Excellent"))
          .when(pl.col("gpa") >= 3.0).then(pl.lit("Very Good"))
          .when(pl.col("gpa") >= 2.5).then(pl.lit("Good"))
          .when(pl.col("gpa") >= 2.0).then(pl.lit("Pass"))
          .otherwise(pl.lit("Weak"))
          .alias("performance_level"),
    ])


def _polars_feature_ops_lazy(path: Path) -> pl.DataFrame:
    """Same operations — Polars lazy with projection pushdown."""
    return (
        pl.scan_parquet(path)
        .select(["student_id", "gpa", "attendance"])
        .with_columns([
            (pl.col("attendance") / 100.0).round(4).alias("attendance_rate"),
            (
                (4.0 - pl.col("gpa"))
                + ((100.0 - pl.col("attendance")) / 25.0)
            ).round(4).alias("academic_risk_score"),
            pl.when(pl.col("gpa") >= 3.5).then(pl.lit("Excellent"))
              .when(pl.col("gpa") >= 3.0).then(pl.lit("Very Good"))
              .when(pl.col("gpa") >= 2.5).then(pl.lit("Good"))
              .when(pl.col("gpa") >= 2.0).then(pl.lit("Pass"))
              .otherwise(pl.lit("Weak"))
              .alias("performance_level"),
        ])
        .collect()
    )


# ═══════════════════════════════════════════════════════════════
# Measurement helpers
# ═══════════════════════════════════════════════════════════════

def _measure_wall_time(func: Callable, *args, **kwargs) -> float:
    """Return wall time in milliseconds."""
    gc.collect()
    start = time.perf_counter()
    func(*args, **kwargs)
    return (time.perf_counter() - start) * 1000.0


def _measure_peak_memory(func: Callable, *args, **kwargs) -> float:
    """Return peak memory in MB.

    LIMITATION: tracemalloc tracks Python allocations; Rust-side
    allocations in Polars may be underreported. This is a
    best-effort portable measure.
    """
    gc.collect()
    tracemalloc.start()
    try:
        func(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / (1024 * 1024)


# ═══════════════════════════════════════════════════════════════
# Benchmark core
# ═══════════════════════════════════════════════════════════════

def _ensure_synthetic(size: int, seed: int = DEFAULT_SEED) -> Path:
    path = SYNTHETIC_DIR / f"students_{size}.parquet"
    if not path.exists():
        logger.info("Generating synthetic dataset: %d rows", size)
        generate_synthetic(size, seed=seed, output_path=path)
    return path


def run_benchmark(size: int) -> dict[str, Any]:
    """Benchmark one size, returning structured results."""
    logger.info("=" * 60)
    logger.info("Benchmarking N = %s", f"{size:,}")
    logger.info("=" * 60)

    path = _ensure_synthetic(size)

    # Load once (fair comparison: both engines see same data)
    logger.info("Loading into Pandas + Polars...")
    pd_df = pd.read_parquet(path)
    pl_df = pl.read_parquet(path)
    logger.info("Pandas shape: %s", pd_df.shape)
    logger.info("Polars shape: %s", (pl_df.height, pl_df.width))

    # ── Warm-up ──
    logger.info("Warm-up (%d run each)...", WARMUP_RUNS)
    for _ in range(WARMUP_RUNS):
        _pandas_feature_ops(pd_df)
        _polars_feature_ops(pl_df)
        _polars_feature_ops_lazy(path)

    # ── Wall time ──
    logger.info("Wall time (%d runs each)...", MEASURED_RUNS)
    pd_times = [
        _measure_wall_time(_pandas_feature_ops, pd_df)
        for _ in range(MEASURED_RUNS)
    ]
    pl_times = [
        _measure_wall_time(_polars_feature_ops, pl_df)
        for _ in range(MEASURED_RUNS)
    ]
    pl_lazy_times = [
        _measure_wall_time(_polars_feature_ops_lazy, path)
        for _ in range(MEASURED_RUNS)
    ]

    pd_median = statistics.median(pd_times)
    pl_median = statistics.median(pl_times)
    pl_lazy_median = statistics.median(pl_lazy_times)

    # ── Peak memory (single run each) ──
    logger.info("Peak memory (single run each)...")
    pd_peak = _measure_peak_memory(_pandas_feature_ops, pd_df)
    pl_peak = _measure_peak_memory(_polars_feature_ops, pl_df)
    pl_lazy_peak = _measure_peak_memory(_polars_feature_ops_lazy, path)

    return {
        "size": size,
        "pandas": {
            "wall_time_ms": round(pd_median, 2),
            "wall_time_all_ms": [round(t, 2) for t in pd_times],
            "peak_memory_mb": round(pd_peak, 2),
        },
        "polars_eager": {
            "wall_time_ms": round(pl_median, 2),
            "wall_time_all_ms": [round(t, 2) for t in pl_times],
            "peak_memory_mb": round(pl_peak, 2),
        },
        "polars_lazy": {
            "wall_time_ms": round(pl_lazy_median, 2),
            "wall_time_all_ms": [round(t, 2) for t in pl_lazy_times],
            "peak_memory_mb": round(pl_lazy_peak, 2),
        },
        "speedup_eager": (
            round(pd_median / pl_median, 2) if pl_median > 0 else 0.0
        ),
        "speedup_lazy": (
            round(pd_median / pl_lazy_median, 2)
            if pl_lazy_median > 0 else 0.0
        ),
    }


# ═══════════════════════════════════════════════════════════════
# Reporting
# ═══════════════════════════════════════════════════════════════

def _print_report(results: list[dict[str, Any]]) -> None:
    print()
    print("=" * 78)
    print("  BENCHMARK — Pandas vs Polars")
    print("=" * 78)

    for r in results:
        print()
        print(f"📊 N = {r['size']:,} rows")
        print("-" * 78)
        print(
            f"  {'Implementation':<20} "
            f"{'Wall (ms)':>12} {'Peak (MB)':>12} {'Speedup':>10}"
        )
        print("-" * 78)

        pd_t = r["pandas"]["wall_time_ms"]
        print(
            f"  {'Pandas (eager)':<20} "
            f"{pd_t:>12.2f} "
            f"{r['pandas']['peak_memory_mb']:>12.2f} "
            f"{'1.00x':>10}"
        )
        print(
            f"  {'Polars (eager)':<20} "
            f"{r['polars_eager']['wall_time_ms']:>12.2f} "
            f"{r['polars_eager']['peak_memory_mb']:>12.2f} "
            f"{r['speedup_eager']:>9.2f}x"
        )
        print(
            f"  {'Polars (lazy)':<20} "
            f"{r['polars_lazy']['wall_time_ms']:>12.2f} "
            f"{r['polars_lazy']['peak_memory_mb']:>12.2f} "
            f"{r['speedup_lazy']:>9.2f}x"
        )
        print()
        print(f"  Pandas runs:      {r['pandas']['wall_time_all_ms']}")
        print(f"  Polars eager runs: {r['polars_eager']['wall_time_all_ms']}")
        print(f"  Polars lazy runs:  {r['polars_lazy']['wall_time_all_ms']}")

    print()
    print("=" * 78)
    print("  ⚠️  Environment-specific results.")
    print("  ⚠️  Windows 11 / Python 3.14.7 / Polars 1.44.2")
    print("  ⚠️  Do NOT generalize to other hardware or datasets.")
    print("=" * 78)
    print()


def _save_json(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "environment": {
            "os": "Windows 11",
            "python": "3.14.7",
            "pandas_version": pd.__version__,
            "polars_version": pl.__version__,
            "numpy_version": np.__version__,
        },
        "methodology": {
            "warmup_runs": WARMUP_RUNS,
            "measured_runs": MEASURED_RUNS,
            "aggregate": "median",
            "operation": "build_base_features (row-wise derived)",
            "memory_measure": "tracemalloc (Python-side, best-effort)",
        },
        "honesty_clause": (
            "Results are environment-specific. They demonstrate "
            "correctness on both engines and the Lazy advantage, "
            "not universal speed claims."
        ),
        "results": results,
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"📁 JSON report: {path}")
    print()


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    parser = argparse.ArgumentParser(
        description=(
            "Benchmark Pandas vs Polars on identical synthetic data."
        )
    )
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=DEFAULT_SIZES,
        help="Row counts to benchmark (default: 100000 1000000)",
    )
    parser.add_argument(
        "--output", type=Path,
        default=REPORTS_DIR / "benchmark_pandas_vs_polars.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    logger.info("Sizes to benchmark: %s", args.sizes)

    results = [run_benchmark(size) for size in args.sizes]

    _print_report(results)
    _save_json(results, args.output)


if __name__ == "__main__":
    main()