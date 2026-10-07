"""
Parquet Writer — Column-Based Storage Utility
==============================================

Provides utility functions for reading and writing Parquet files,
plus size comparison against CSV to quantify columnar compression.

Why Parquet?
    - Column-based storage (Ch 4 of the guide)
    - 70–80% size reduction vs CSV
    - Predicate pushdown → reads only needed columns
    - Preserves schema (dtypes, nullable)
    - Native support in Pandas, Polars, Spark

Usage:
    from src.warehouse.parquet_writer import write_parquet, read_parquet
    write_parquet(df, Path("data/gold/fact.parquet"))
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_COMPRESSION: str = "snappy"
"""Parquet compression algorithm.

Options:
    - snappy : fast, moderate ratio (default)
    - gzip   : slower, better ratio
    - brotli : slowest, best ratio
    - lz4    : very fast, low ratio
    - zstd   : balanced (modern recommendation)
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_parquet(
    df: pd.DataFrame,
    file_path: Path,
    compression: str = DEFAULT_COMPRESSION,
) -> Path:
    """Write a DataFrame to a Parquet file.

    Args:
        df:          DataFrame to persist.
        file_path:   Target .parquet path.
        compression: Compression algorithm (default: snappy).

    Returns:
        Path to the written file.

    Raises:
        ValueError: If df is empty.
    """
    if df.empty:
        raise ValueError("Cannot write an empty DataFrame to Parquet.")

    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(
        file_path,
        engine="pyarrow",
        compression=compression,
        index=False,
    )

    size_kb = file_path.stat().st_size / 1024
    logger.info(
        "Wrote %d rows x %d cols -> %s (%.2f KB, %s)",
        len(df), len(df.columns), file_path, size_kb, compression,
    )
    return file_path


def read_parquet(
    file_path: Path,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame.

    Args:
        file_path: Source .parquet path.
        columns:   Optional subset of columns (predicate pushdown).

    Returns:
        DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    df = pd.read_parquet(file_path, engine="pyarrow", columns=columns)

    logger.info(
        "Read %d rows x %d cols from %s",
        len(df), len(df.columns), file_path,
    )
    return df


def compare_csv_vs_parquet(csv_path: Path) -> dict[str, Any]:
    """Compare storage efficiency of CSV vs Parquet.

    Args:
        csv_path: Path to a CSV file.

    Returns:
        Dict with sizes, ratio, and compression percentage.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Write to a temporary parquet for comparison
    tmp_parquet = csv_path.with_suffix(".parquet.tmp")
    try:
        df.to_parquet(tmp_parquet, engine="pyarrow", compression=DEFAULT_COMPRESSION, index=False)

        csv_size = csv_path.stat().st_size
        parquet_size = tmp_parquet.stat().st_size
        ratio = parquet_size / csv_size if csv_size > 0 else 0

        result = {
            "csv_bytes": csv_size,
            "parquet_bytes": parquet_size,
            "ratio": round(ratio, 3),
            "compression_pct": round((1 - ratio) * 100, 1),
            "rows": len(df),
            "columns": len(df.columns),
        }

        logger.info(
            "CSV: %d B | Parquet: %d B | Compression: %.1f%%",
            csv_size, parquet_size, result["compression_pct"],
        )
        return result
    finally:
        tmp_parquet.unlink(missing_ok=True)


def get_parquet_info(file_path: Path) -> dict[str, Any]:
    """Return metadata about a Parquet file.

    Args:
        file_path: Path to a Parquet file.

    Returns:
        Dict with rows, columns, dtypes, size, column names.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    df = pd.read_parquet(file_path, engine="pyarrow")

    return {
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


# ---------------------------------------------------------------------------
# Standalone demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    ROOT = Path(__file__).resolve().parent.parent.parent
    csv_file = ROOT / "data/processed/csv/csv_clean.csv"

    if csv_file.exists():
        result = compare_csv_vs_parquet(csv_file)
        print()
        print("=" * 60)
        print("CSV vs Parquet — Compression Report")
        print("=" * 60)
        for key, value in result.items():
            print(f"  {key:<20}: {value}")
        print("=" * 60)
    else:
        print(f"CSV file not found: {csv_file}")