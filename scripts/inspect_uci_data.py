"""Inspect UCI Student Performance dataset before ETL.

Reads student-mat.csv and student-por.csv (semicolon-separated),
validates structure, prints summary, and simulates the planned
transformation to the unified schema.

Usage:
    python scripts/inspect_uci_data.py
    python scripts/inspect_uci_data.py --raw-dir data/raw/uci
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "uci"

# UCI column order (33 columns)
UCI_COLUMNS = [
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "guardian",
    "traveltime", "studytime", "failures", "schoolsup", "famsup",
    "paid", "activities", "nursery", "higher", "internet",
    "romantic", "famrel", "freetime", "goout", "Dalc", "Walc",
    "health", "absences", "G1", "G2", "G3",
]

# Columns that should be int (currently stored as quoted strings)
INT_COLUMNS = [
    "age", "Medu", "Fedu", "traveltime", "studytime", "failures",
    "famrel", "freetime", "goout", "Dalc", "Walc", "health",
    "absences", "G1", "G2", "G3",
]

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Loading
# ─────────────────────────────────────────────────────────────

def load_uci_csv(path: Path) -> pd.DataFrame:
    """Load a UCI CSV with semicolon separator and quoted values.

    Args:
        path: Path to student-mat.csv or student-por.csv.

    Returns:
        DataFrame with all columns as strings (initial read).

    Raises:
        FileNotFoundError: if path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(
        path,
        sep=";",
        quotechar='"',
        dtype=str,      # keep strings for inspection
        encoding="utf-8",
    )
    logger.info("Loaded %s: shape=%s", path.name, df.shape)
    return df


def cast_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Cast int columns from quoted strings to actual ints."""
    df = df.copy()
    for col in INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
    return df


# ─────────────────────────────────────────────────────────────
# Inspection
# ─────────────────────────────────────────────────────────────

def inspect(df: pd.DataFrame, name: str) -> None:
    """Print structural summary for a single UCI file."""
    print()
    print("=" * 70)
    print(f"FILE: {name}")
    print("=" * 70)
    print(f"Rows:    {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print()

    print("Column dtypes (after cast attempt):")
    with pd.option_context("display.max_rows", None):
        print(df.dtypes.to_string())
    print()

    print("First 3 rows (selected columns):")
    selected = ["school", "sex", "age", "address", "absences", "G1", "G2", "G3"]
    with pd.option_context("display.width", 200):
        print(df[selected].head(3).to_string(index=False))
    print()

    # Numeric ranges
    print("Numeric ranges:")
    for col in ["age", "absences", "G1", "G2", "G3"]:
        if col in df.columns:
            s = df[col]
            print(f"  {col:10s}: min={s.min():>4}, max={s.max():>4}, "
                  f"mean={s.mean():>7.2f}, std={s.std():>6.2f}")
    print()

    # Categorical value counts
    print("Categorical distributions:")
    for col in ["school", "sex", "address", "famsize", "Pstatus"]:
        if col in df.columns:
            counts = df[col].value_counts().to_dict()
            print(f"  {col:10s}: {counts}")
    print()

    # Missing values check
    null_counts = df.isna().sum().sum()
    print(f"Total missing values: {null_counts}")


def simulate_transform(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Simulate the planned transformation to unified schema.

    Returns a DataFrame with: student_id, name, age, gender, city,
    gpa, attendance_rate, n_assessments, score_change, course.
    """
    n = len(df)
    out = pd.DataFrame({
        "student_id":      [f"S{i:04d}" for i in range(n)],
        "name":            [f"Student_{i:04d}" for i in range(n)],
        "age":             df["age"].astype("Int64"),
        "gender":          df["sex"].map({"M": "Male", "F": "Female"}),
        "city":            df["school"] + "-" + df["address"],  # 4 values
        "gpa":             (df["G3"] / 5.0).round(2),
        "attendance_rate": (1.0 - df["absences"] / 100.0).clip(0, 1).round(3),
        "n_assessments":   3,
        "score_change":    (df["G3"] - df["G1"]).astype("Int64"),
        "course":          source,
    })
    return out


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect UCI Student Performance CSVs.")
    p.add_argument(
        "--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
        help="Directory containing student-mat.csv and student-por.csv.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    print()
    print("UCI Student Performance — Inspection")
    print(f"Source directory: {args.raw_dir}")

    files = {
        "math":       args.raw_dir / "student-mat.csv",
        "portuguese": args.raw_dir / "student-por.csv",
    }

    dfs: dict[str, pd.DataFrame] = {}
    for name, path in files.items():
        try:
            df = cast_columns(load_uci_csv(path))
            dfs[name] = df
            inspect(df, path.name)
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return 1

    # ─── Combined view ───
    print()
    print("=" * 70)
    print("COMBINED SUMMARY")
    print("=" * 70)
    total = sum(len(df) for df in dfs.values())
    print(f"Total rows:  {total}")
    print(f"Unique students (by 14-key merge): ...")

    # Simulate merge (R script keys)
    merge_keys = [
        "school", "sex", "age", "address", "famsize", "Pstatus",
        "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet",
    ]
    mat = dfs["math"]
    por = dfs["portuguese"]
    merged = mat.merge(por, on=merge_keys, how="inner", suffixes=("_mat", "_por"))
    print(f"  Intersection (students in both): {len(merged)}")
    print(f"  Unique students:                 {total - len(merged)}")

    # ─── Simulated transform preview ───
    print()
    print("=" * 70)
    print("SIMULATED TRANSFORM (first 5 rows of math)")
    print("=" * 70)
    sim = simulate_transform(mat, "math")
    with pd.option_context("display.width", 220, "display.max_columns", None):
        print(sim.head(5).to_string(index=False))

    print()
    print("=" * 70)
    print("TRANSFORM STATISTICS (math)")
    print("=" * 70)
    print(f"  gpa range:             [{sim['gpa'].min()}, {sim['gpa'].max()}]")
    print(f"  attendance_rate range: [{sim['attendance_rate'].min()}, {sim['attendance_rate'].max()}]")
    print(f"  score_change range:    [{sim['score_change'].min()}, {sim['score_change'].max()}]")
    print(f"  cities:                {sorted(sim['city'].unique())}")
    print(f"  genders:               {sorted(sim['gender'].unique())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())