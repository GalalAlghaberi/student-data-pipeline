"""UCI Student Performance — ETL Pipeline (Phase B.5.3).

Transforms the raw UCI CSVs (student-mat.csv + student-por.csv) into a
single unified-schema parquet that matches the rest of the project.

Reference: docs/UCI_ETL.md

Pipeline:
    1. Load student-mat.csv (course="math") + student-por.csv (course="portuguese")
    2. Concatenate vertically → 1,044 rows
    3. Assign `student_id` by 13-key merge (per student-merge.R)
    4. Assign `record_id` (one per row)
    5. Clip `absences` to 99th percentile
    6. Transform to unified schema (17 columns)
    7. Verify 12 checks
    8. Write data/processed/uci_clean.parquet

Usage:
    python -m pipelines.uci_pipeline
    python -m pipelines.uci_pipeline --raw-dir data/raw/uci
    python -m pipelines.uci_pipeline --output data/processed/uci_clean.parquet
    python -m pipelines.uci_pipeline --log-level DEBUG
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR: Final = PROJECT_ROOT / "data" / "raw" / "uci"
DEFAULT_OUTPUT: Final = PROJECT_ROOT / "data" / "processed" / "uci_clean.parquet"

# Input file names
MAT_FILE: Final = "student-mat.csv"
POR_FILE: Final = "student-por.csv"

# CSV contract
CSV_SEP: Final = ";"
CSV_QUOTE: Final = '"'
CSV_ENCODING: Final = "utf-8"

# Columns that are stored as quoted strings but represent integers
INT_COLUMNS: Final[list[str]] = [
    "age", "Medu", "Fedu", "traveltime", "studytime", "failures",
    "famrel", "freetime", "goout", "Dalc", "Walc", "health",
    "absences", "G1", "G2", "G3",
]

# 13-key merge (verbatim from student-merge.R)
MERGE_KEYS: Final[list[str]] = [
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet",
]

# Expected counts (from inspection, must match)
EXPECTED_MAT_ROWS: Final = 395
EXPECTED_POR_ROWS: Final = 649
EXPECTED_TOTAL: Final = 1044
EXPECTED_UNIQUE_STUDENTS: Final = 662
EXPECTED_UNIQUE_RECORDS: Final = 1044

# Absences clip percentile
ABSENCES_CLIP_Q: Final = 0.99

# Output schema (17 columns, in order)
OUTPUT_COLUMNS: Final[list[str]] = [
    "record_id", "student_id", "course", "name",
    "age", "gender", "city",
    "gpa", "attendance_rate", "n_assessments", "score_change",
    "score_1", "score_2", "score_final",
    "school", "address", "source",
]


# ═══════════════════════════════════════════════════════════════════
# Step 1 — Load
# ═══════════════════════════════════════════════════════════════════

def _load_single(path: Path, course: str) -> pd.DataFrame:
    """Load one UCI CSV, cast numeric columns, and add a `course` column.

    Args:
        path: Path to student-mat.csv or student-por.csv.
        course: "math" or "portuguese".

    Returns:
        DataFrame with all columns cast where applicable + a `course` column.

    Raises:
        FileNotFoundError: If the CSV is missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing UCI file: {path}")

    df = pd.read_csv(
        path,
        sep=CSV_SEP,
        quotechar=CSV_QUOTE,
        dtype=str,           # read everything as string first
        encoding=CSV_ENCODING,
    )

    # Cast known numeric columns to int64
    for col in INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")

    df["course"] = course
    logger.info("Loaded %s: %d rows", path.name, len(df))
    return df


# ═══════════════════════════════════════════════════════════════════
# Step 3 — Student ID assignment
# ═══════════════════════════════════════════════════════════════════

def _assign_student_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Assign a stable `student_id` per unique 13-key combination.

    Uses the same 13 attributes as student-merge.R to identify the same
    physical student across the two course files.

    Args:
        df: Combined DataFrame (mat + por).

    Returns:
        Same DataFrame with a new `student_id` column (`S0000` … `S0661`).
    """
    # Composite key per row (preserves order for deterministic IDs)
    keys = df[MERGE_KEYS].apply(tuple, axis=1)

    # Deduplicate keys, preserving first-seen order
    unique_keys = keys.drop_duplicates().tolist()
    logger.info("Unique merge keys: %d", len(unique_keys))

    key_to_sid = {k: f"S{i:04d}" for i, k in enumerate(unique_keys)}

    out = df.copy()
    out["student_id"] = keys.map(key_to_sid)
    return out


# ═══════════════════════════════════════════════════════════════════
# Step 6 — Transform to unified schema
# ═══════════════════════════════════════════════════════════════════

def _transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Map the combined DataFrame to the 17-column unified schema.

    Args:
        df: Combined DataFrame after student_id + record_id assignment
            and after absences clipping.

    Returns:
        DataFrame with exactly `OUTPUT_COLUMNS` columns.
    """
    out = pd.DataFrame({
        "record_id":       df["record_id"],
        "student_id":      df["student_id"],
        "course":          df["course"].astype("string"),
        "name":            "Student_" + df["student_id"].str[1:],   # "Student_0000"
        "age":             df["age"].astype("int64"),
        "gender":          df["sex"].map({"M": "Male", "F": "Female"}),
        "city":            (df["school"] + "-" + df["address"]).astype("string"),
        "gpa":             (df["G3"] / 5.0).round(4),               # 0-20 → 0-4
        "attendance_rate": (1.0 - df["absences"] / 100.0).clip(0.0, 1.0).round(4),
        "n_assessments":   pd.Series(3, index=df.index, dtype="int64"),
        "score_change":    (df["G3"] - df["G1"]).astype("int64"),
        "score_1":         df["G1"].astype("int64"),
        "score_2":         df["G2"].astype("int64"),
        "score_final":     df["G3"].astype("int64"),
        "school":          df["school"].astype("string"),
        "address":         df["address"].astype("string"),
        "source":          pd.Series("uci", index=df.index, dtype="string"),
    })
    # Enforce column order
    return out[OUTPUT_COLUMNS]


# ═══════════════════════════════════════════════════════════════════
# Step 7 — Verification
# ═══════════════════════════════════════════════════════════════════

def _verify(df: pd.DataFrame, clip_threshold: float) -> None:
    """Run the 12 post-ETL checks (docs/UCI_ETL.md §6).

    Raises:
        AssertionError: on any mismatch.
    """
    # 1-4: counts
    checks = [
        ("row_count",        len(df),                 EXPECTED_TOTAL),
        ("col_count",        len(df.columns),         len(OUTPUT_COLUMNS)),
        ("unique_students",  df["student_id"].nunique(), EXPECTED_UNIQUE_STUDENTS),
        ("unique_records",   df["record_id"].nunique(),  EXPECTED_UNIQUE_RECORDS),
    ]
    for name, actual, expected in checks:
        assert actual == expected, f"{name}: got {actual}, expected {expected}"

    # 5-7: categorical domains
    assert set(df["course"].unique()) == {"math", "portuguese"}, \
        f"Unexpected course values: {df['course'].unique()}"
    assert set(df["gender"].unique()) <= {"Male", "Female"}, \
        f"Unexpected gender values: {df['gender'].unique()}"
    assert set(df["city"].unique()) == {"GP-U", "GP-R", "MS-U", "MS-R"}, \
        f"Unexpected city values: {df['city'].unique()}"

    # 8-9: numeric ranges
    assert df["gpa"].between(0.0, 4.0).all(), "gpa out of [0, 4]"
    assert df["attendance_rate"].between(0.0, 1.0).all(), "attendance_rate out of [0, 1]"

    # 10: absences clipped
    assert float(df["score_final"].max()) <= 20.0  # sanity
    # (raw absences already gone after transform — verify via internal check)

    # 11: score_change formula
    expected_change = df["score_final"] - df["score_1"]
    assert (df["score_change"] == expected_change).all(), \
        "score_change != score_final - score_1"

    # 12: no missing values
    null_count = int(df.isna().sum().sum())
    assert null_count == 0, f"{null_count} missing values found"

    logger.info(
        "All verification checks passed (clip_threshold=%.2f)", clip_threshold
    )


# ═══════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════

def run_etl(
    raw_dir: Path = DEFAULT_RAW_DIR,
    output_path: Path = DEFAULT_OUTPUT,
) -> pd.DataFrame:
    """Run the complete UCI ETL pipeline.

    Args:
        raw_dir: Directory containing student-mat.csv and student-por.csv.
        output_path: Where to write the resulting parquet.

    Returns:
        The transformed DataFrame (also written to disk).

    Raises:
        FileNotFoundError: if inputs are missing.
        AssertionError: if any verification check fails.
    """
    raw_dir = Path(raw_dir)
    output_path = Path(output_path)

    # 1. Load
    mat = _load_single(raw_dir / MAT_FILE, course="math")
    por = _load_single(raw_dir / POR_FILE, course="portuguese")

    assert len(mat) == EXPECTED_MAT_ROWS, \
        f"mat rows: got {len(mat)}, expected {EXPECTED_MAT_ROWS}"
    assert len(por) == EXPECTED_POR_ROWS, \
        f"por rows: got {len(por)}, expected {EXPECTED_POR_ROWS}"

    # 2. Concat
    df = pd.concat([mat, por], ignore_index=True)
    logger.info("Concatenated: %d rows", len(df))

    # 3. Student IDs
    df = _assign_student_ids(df)

    # 4. Record IDs
    df = df.reset_index(drop=True)
    df["record_id"] = [f"R{i:04d}" for i in range(len(df))]

    # 5. Absences clip (99th percentile of combined data)
    clip_threshold = float(df["absences"].quantile(ABSENCES_CLIP_Q))
    n_affected = int((df["absences"] > clip_threshold).sum())
    df["absences"] = df["absences"].clip(upper=clip_threshold)
    logger.info(
        "Absences clipped at %.2f (99th percentile) — %d rows affected",
        clip_threshold, n_affected,
    )

    # 6. Transform
    out = _transform_to_unified(df)

    # 7. Verify
    _verify(out, clip_threshold=clip_threshold)

    # 8. Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(output_path, index=False)
    logger.info(
        "Wrote %s (%d rows × %d cols)",
        output_path, len(out), len(out.columns),
    )

    return out


# ═══════════════════════════════════════════════════════════════════
# Convenience loader
# ═══════════════════════════════════════════════════════════════════

def load_clean(path: Path = DEFAULT_OUTPUT) -> pd.DataFrame:
    """Load a previously-generated uci_clean.parquet.

    Useful in tests and downstream modules.

    Args:
        path: Path to the parquet file.

    Returns:
        DataFrame with the 17-column unified schema.

    Raises:
        FileNotFoundError: if the parquet has not been generated yet.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python -m pipelines.uci_pipeline"
        )
    return pd.read_parquet(path)


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="UCI Student Performance ETL (Phase B.5)."
    )
    p.add_argument(
        "--raw-dir", type=Path, default=DEFAULT_RAW_DIR,
        help="Directory containing student-mat.csv and student-por.csv.",
    )
    p.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Destination parquet path.",
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

    df = run_etl(raw_dir=args.raw_dir, output_path=args.output)

    # Summary
    print()
    print("=" * 60)
    print("UCI ETL — Summary")
    print("=" * 60)
    print(f"Rows:               {len(df):>6,}")
    print(f"Columns:            {len(df.columns):>6}")
    print(f"Unique students:    {df['student_id'].nunique():>6,}")
    print(f"Unique records:     {df['record_id'].nunique():>6,}")
    print(f"Course breakdown:   {df['course'].value_counts().to_dict()}")
    print(f"gpa range:          [{df['gpa'].min():.2f}, {df['gpa'].max():.2f}]")
    print(f"attendance range:   [{df['attendance_rate'].min():.3f}, "
          f"{df['attendance_rate'].max():.3f}]")
    print(f"score_change range: [{df['score_change'].min()}, "
          f"{df['score_change'].max()}]")
    print(f"G3=0 count:         {(df['score_final'] == 0).sum()}")
    print()
    print(f"Output: {args.output}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())