"""Silver Merge — Phase B.6.

Unifies 8 data sources (UCI parquet + 7 base CSVs) into a single
17-column dataset written to data/silver/.

Reference: docs/SILVER_MERGE.md

Pipeline:
    1. Load UCI (data/processed/uci_clean.parquet) → 1,044 rows
    2. Load 7 base sources (data/processed/*/[name]_clean.csv)
    3. Transform each to unified 17-column schema
    4. Concat all → ~1,136 rows
    5. Verify invariants
    6. Write data/silver/unified_students.parquet
    7. Write data/silver/quality_report.json

Usage:
    python -m src.warehouse.silver_merge
    python -m src.warehouse.silver_merge --processed-dir data/processed
    python -m src.warehouse.silver_merge --output-dir data/silver
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent.parent
DEFAULT_PROCESSED_DIR: Final = PROJECT_ROOT / "data" / "processed"
DEFAULT_OUTPUT_DIR: Final = PROJECT_ROOT / "data" / "silver"

UCI_FILE: Final = "uci_clean.parquet"

# The 7 base sources (in priority order for reporting)
BASE_SOURCES: Final[list[str]] = [
    "api", "csv", "json", "mongodb", "postgres", "scraper", "sqlite",
]

# Unified 17-column schema (matches uci_clean.parquet)
UNIFIED_COLUMNS: Final[list[str]] = [
    "record_id", "student_id", "course", "name",
    "age", "gender", "city",
    "gpa", "attendance_rate", "n_assessments", "score_change",
    "score_1", "score_2", "score_final",
    "school", "address", "source",
]

# Columns that must be non-null
NON_NULL_COLUMNS: Final[list[str]] = ["record_id", "student_id", "source"]

# Base schema columns (from pipelines/base_pipeline.py)
BASE_COLUMNS: Final[list[str]] = ["student_id", "name", "age", "gpa", "attendance", "city"]

# Output filenames
OUTPUT_PARQUET: Final = "unified_students.parquet"
OUTPUT_REPORT: Final = "quality_report.json"


# ═══════════════════════════════════════════════════════════════════
# Loading
# ═══════════════════════════════════════════════════════════════════

def load_uci(processed_dir: Path) -> pd.DataFrame | None:
    """Load the UCI parquet if it exists.

    Args:
        processed_dir: Directory containing uci_clean.parquet.

    Returns:
        DataFrame or None if file is missing.
    """
    path = processed_dir / UCI_FILE
    if not path.exists():
        logger.warning("UCI parquet missing: %s — skipping", path)
        return None
    df = pd.read_parquet(path)
    logger.info("Loaded UCI: %d rows × %d cols", len(df), len(df.columns))
    return df


def load_base(processed_dir: Path, source: str) -> pd.DataFrame | None:
    """Load one base source CSV if it exists.

    Args:
        processed_dir: Root of data/processed.
        source: One of BASE_SOURCES.

    Returns:
        DataFrame or None if file is missing.
    """
    path = processed_dir / source / f"{source}_clean.csv"
    if not path.exists():
        logger.warning("Base source missing: %s — skipping", path)
        return None
    df = pd.read_csv(path)
    logger.info("Loaded %s: %d rows", source, len(df))
    return df


# ═══════════════════════════════════════════════════════════════════
# Transformation
# ═══════════════════════════════════════════════════════════════════

def _transform_uci(df: pd.DataFrame) -> pd.DataFrame:
    """Regenerate `record_id` for UCI (source-prefixed).

    Args:
        df: Output of load_uci() — already 17-column schema.

    Returns:
        Copy with regenerated record_id.
    """
    out = df.copy()
    n = len(out)
    out["record_id"] = [f"R-uci-{i:04d}" for i in range(n)]
    return out[UNIFIED_COLUMNS]


def _transform_base(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Transform a 6-column base DataFrame to the unified schema.

    Args:
        df: Base DataFrame with columns: student_id, name, age, gpa,
            attendance, city.
        source: Source name (used for `source` and `record_id` prefix).

    Returns:
        DataFrame with exactly 17 columns.
    """
    n = len(df)

    # Validate attendance range (0-100). Some sources might already be 0-1.
    att = pd.to_numeric(df["attendance"], errors="coerce")
    att_max = float(att.max()) if att.notna().any() else 0.0
    if att_max > 1.1 and att_max <= 100.0:
        attendance_rate = (att / 100.0).clip(0.0, 1.0)
    elif att_max <= 1.1:
        # Already in [0,1] — keep as-is (log a warning)
        logger.warning(
            "%s: attendance appears to be already 0-1 (max=%.3f); keeping as-is",
            source, att_max,
        )
        attendance_rate = att.clip(0.0, 1.0)
    else:
        raise ValueError(
            f"{source}: attendance max={att_max} outside valid ranges (0-1 or 0-100)"
        )

    out = pd.DataFrame({
        "record_id":       [f"R-{source}-{i:04d}" for i in range(n)],
        "student_id":      df["student_id"].astype("string"),
        "course":          pd.array([pd.NA] * n, dtype="string"),
        "name":            df["name"].astype("string"),
        "age":             pd.to_numeric(df["age"], errors="coerce").astype("Int64"),
        "gender":          pd.array([pd.NA] * n, dtype="string"),
        "city":            df["city"].astype("string"),
        "gpa":             pd.to_numeric(df["gpa"], errors="coerce").astype("Float64"),
        "attendance_rate": attendance_rate.astype("Float64"),
        "n_assessments":   pd.array([pd.NA] * n, dtype="Int64"),
        "score_change":    pd.array([pd.NA] * n, dtype="Int64"),
        "score_1":         pd.array([pd.NA] * n, dtype="Int64"),
        "score_2":         pd.array([pd.NA] * n, dtype="Int64"),
        "score_final":     pd.array([pd.NA] * n, dtype="Int64"),
        "school":          pd.array([pd.NA] * n, dtype="string"),
        "address":         pd.array([pd.NA] * n, dtype="string"),
        "source":          pd.array([source] * n, dtype="string"),
    })
    return out[UNIFIED_COLUMNS]


# ═══════════════════════════════════════════════════════════════════
# Verification
# ═══════════════════════════════════════════════════════════════════

def _verify(df: pd.DataFrame) -> None:
    """Run invariant checks on the merged DataFrame.

    Raises:
        AssertionError: on any violation.
    """
    # Column contract
    assert list(df.columns) == UNIFIED_COLUMNS, \
        f"Column mismatch: {list(df.columns)}"

    # No NaN in mandatory columns
    for col in NON_NULL_COLUMNS:
        nulls = int(df[col].isna().sum())
        assert nulls == 0, f"{col} has {nulls} NaN (must be non-null)"

    # record_id uniqueness
    n_dup = int(df["record_id"].duplicated().sum())
    assert n_dup == 0, f"{n_dup} duplicate record_id values"

    # source values
    valid_sources = set(BASE_SOURCES) | {"uci"}
    actual_sources = set(df["source"].dropna().unique())
    extra = actual_sources - valid_sources
    assert not extra, f"Unexpected source values: {extra}"

    # numeric ranges where present
    if df["gpa"].notna().any():
        assert df.loc[df["gpa"].notna(), "gpa"].between(0.0, 4.0).all(), \
            "gpa outside [0, 4]"
    if df["attendance_rate"].notna().any():
        assert df.loc[df["attendance_rate"].notna(), "attendance_rate"].between(0.0, 1.0).all(), \
            "attendance_rate outside [0, 1]"

    logger.info("All verification checks passed (%d rows)", len(df))


# ═══════════════════════════════════════════════════════════════════
# Quality report
# ═══════════════════════════════════════════════════════════════════

def build_quality_report(df: pd.DataFrame) -> dict:
    """Build per-source and per-column coverage report.

    Args:
        df: Merged DataFrame.

    Returns:
        Nested dict (JSON-serializable).
    """
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "sources": {},
        "column_coverage": {},
    }

    # Per-source stats
    for src, group in df.groupby("source"):
        report["sources"][str(src)] = {
            "rows": int(len(group)),
            "gpa_filled": int(group["gpa"].notna().sum()),
            "attendance_filled": int(group["attendance_rate"].notna().sum()),
        }

    # Per-column coverage (fraction non-null)
    total = len(df)
    for col in df.columns:
        non_null = int(df[col].notna().sum())
        report["column_coverage"][col] = round(non_null / total, 4) if total else 0.0

    return report


def save_quality_report(report: dict, output_dir: Path) -> Path:
    """Write the JSON report to disk (NaN → null)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / OUTPUT_REPORT
    path.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info("Wrote quality report: %s", path)
    return path


# ═══════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════

def run_merge(
    processed_dir: Path = DEFAULT_PROCESSED_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> pd.DataFrame:
    """Run the full Silver Merge.

    Args:
        processed_dir: Root of data/processed.
        output_dir: Destination for data/silver/.

    Returns:
        The merged DataFrame (also written to disk).
    """
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)

    parts: list[pd.DataFrame] = []

    # 1. UCI
    uci = load_uci(processed_dir)
    if uci is not None:
        parts.append(_transform_uci(uci))

    # 2. Base sources
    for src in BASE_SOURCES:
        base = load_base(processed_dir, src)
        if base is None:
            continue
        parts.append(_transform_base(base, source=src))

    if not parts:
        raise RuntimeError("No sources available to merge — check data/processed/")

    # 3. Concat
    merged = pd.concat(parts, ignore_index=True)
    logger.info("Merged: %d rows from %d sources",
                len(merged), len(parts))

    # 4. Verify
    _verify(merged)

    # 5. Write parquet
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / OUTPUT_PARQUET
    merged.to_parquet(parquet_path, index=False)
    logger.info("Wrote %s (%d rows × %d cols)",
                parquet_path, len(merged), len(merged.columns))

    # 6. Quality report
    report = build_quality_report(merged)
    save_quality_report(report, output_dir)

    return merged


def load_unified(output_dir: Path = DEFAULT_OUTPUT_DIR) -> pd.DataFrame:
    """Load a previously-generated unified_students.parquet.

    Args:
        output_dir: Directory containing unified_students.parquet.

    Returns:
        DataFrame.

    Raises:
        FileNotFoundError: if not generated yet.
    """
    path = Path(output_dir) / OUTPUT_PARQUET
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python -m src.warehouse.silver_merge"
        )
    return pd.read_parquet(path)


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Silver Merge (Phase B.6).")
    p.add_argument(
        "--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR,
        help="Root of data/processed.",
    )
    p.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Destination for data/silver/.",
    )
    p.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    df = run_merge(processed_dir=args.processed_dir, output_dir=args.output_dir)

    # Summary
    print()
    print("=" * 62)
    print("Silver Merge — Summary")
    print("=" * 62)
    print(f"Total rows:        {len(df):>6,}")
    print(f"Total columns:     {len(df.columns):>6}")
    print()
    print("Per-source breakdown:")
    counts = df["source"].value_counts().sort_index()
    for src, n in counts.items():
        gpa_filled = int(df.loc[df["source"] == src, "gpa"].notna().sum())
        print(f"  {src:<10}: {n:>5} rows  (gpa filled: {gpa_filled})")
    print()
    print(f"gpa coverage:      {df['gpa'].notna().mean():.4f}")
    print(f"attendance cover.: {df['attendance_rate'].notna().mean():.4f}")
    print()
    print(f"Output parquet:    {args.output_dir / OUTPUT_PARQUET}")
    print(f"Quality report:    {args.output_dir / OUTPUT_REPORT}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())