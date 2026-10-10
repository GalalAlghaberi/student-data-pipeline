"""ML Data Layer v2 — Phase B.7 (Scale-Up).

Loads the Phase B.6 Silver dataset, filters to UCI-only rows (N=1,044),
and produces (X, y, groups) tuples for GroupKFold-based training.

Leakage re-audit (docs/ML_EXPERIMENTS_SCALE.md §3):
  Excluded (algebraic leak):
    - score_final    (gpa = score_final / 5.0)
    - score_change   (score_final - score_1)

  Excluded (zero variance over UCI-only):
    - n_assessments  (constant = 3)
    - source         (constant = "uci")

  Excluded (collinear with `city`):
    - school, address

  Excluded (identifier / text):
    - record_id, student_id (student_id kept as CV group only)
    - name

Two feature sets (docs/ML_EXPERIMENTS_SCALE.md §4):
  FS-A (demographic-only baseline):
    numeric:      attendance_rate, age
    categorical:  gender, city, course

  FS-B (temporal signal augmentation):
    FS-A + numeric: score_1, score_2

Golden Rules:
  - Add a layer; do not replace (v1 stays intact).
  - No OneHotEncoder here — encoding happens per fold in pipeline_v2.
  - Deterministic (no random_state needed; no date arithmetic).
  - No changes to src/features/, src/warehouse/, or src/ml/* (v1).

Reference: docs/ML_EXPERIMENTS_SCALE.md §2, §3, §4
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, Literal

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SILVER_DIR_DEFAULT = PROJECT_ROOT / "data" / "silver"
SILVER_PARQUET = "unified_students.parquet"

TARGET: Final = "gpa"
GROUP_COLUMN: Final = "student_id"
SOURCE_COLUMN: Final = "source"
UCI_SOURCE_VALUE: Final = "uci"

# Row-count invariants (from Phase B.5 + B.6)
EXPECTED_UCI_ROWS: Final = 1044
EXPECTED_UNIQUE_STUDENTS: Final = 662
EXPECTED_MULTI_RECORD_STUDENTS: Final = 369

# ─── Feature set A (demographic-only baseline) ──────────────────
FS_A_NUMERIC: Final[list[str]] = ["attendance_rate", "age"]
FS_A_CATEGORICAL: Final[list[str]] = ["gender", "city", "course"]

# ─── Feature set B (temporal signal augmentation) ───────────────
FS_B_NUMERIC: Final[list[str]] = FS_A_NUMERIC + ["score_1", "score_2"]
FS_B_CATEGORICAL: Final[list[str]] = FS_A_CATEGORICAL

# ─── Excluded columns (documented for traceability + tests) ─────
EXCLUDED_LEAKY: Final[list[str]] = ["score_final", "score_change"]
EXCLUDED_ZERO_VAR: Final[list[str]] = ["n_assessments", "source"]
EXCLUDED_COLLINEAR: Final[list[str]] = ["school", "address"]
EXCLUDED_ID: Final[list[str]] = ["record_id", "student_id"]
EXCLUDED_TEXT: Final[list[str]] = ["name"]

# Flat union for defensive checks
ALL_EXCLUDED: Final[list[str]] = (
    EXCLUDED_LEAKY
    + EXCLUDED_ZERO_VAR
    + EXCLUDED_COLLINEAR
    + EXCLUDED_ID
    + EXCLUDED_TEXT
)

FeatureSet = Literal["A", "B"]


# ═══════════════════════════════════════════════════════════════
# Loading
# ═══════════════════════════════════════════════════════════════

def load_uci_only(silver_dir: Path | str = SILVER_DIR_DEFAULT) -> pd.DataFrame:
    """Load Silver dataset and filter to UCI-only rows.

    Args:
        silver_dir: Directory containing unified_students.parquet.

    Returns:
        DataFrame with exactly 1,044 UCI rows × 17 columns.

    Raises:
        FileNotFoundError: If unified_students.parquet is missing.
        ValueError: If `source` column is absent.
        AssertionError: If row count, gpa-completeness, group-completeness,
            or unique-student-count invariants fail.
    """
    silver_dir = Path(silver_dir)
    path = silver_dir / SILVER_PARQUET
    if not path.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {path}\n"
            "Run: python -m src.warehouse.silver_merge"
        )

    df_full = pd.read_parquet(path)
    logger.info(
        "Loaded Silver: shape=%s, columns=%d",
        df_full.shape, df_full.shape[1],
    )

    if SOURCE_COLUMN not in df_full.columns:
        raise ValueError(f"Silver parquet missing `{SOURCE_COLUMN}` column")

    df = df_full[df_full[SOURCE_COLUMN] == UCI_SOURCE_VALUE].copy()
    logger.info("Filtered to UCI-only: %d rows", len(df))

    # Invariant 1 — exact row count
    assert len(df) == EXPECTED_UCI_ROWS, (
        f"Expected {EXPECTED_UCI_ROWS} UCI rows, got {len(df)}"
    )

    # Invariant 2 — no NaN in target
    n_nan_gpa = int(df[TARGET].isna().sum())
    assert n_nan_gpa == 0, (
        f"UCI rows contain {n_nan_gpa} NaN `{TARGET}` values (expected 0)"
    )

    # Invariant 3 — no NaN in group column
    n_nan_group = int(df[GROUP_COLUMN].isna().sum())
    assert n_nan_group == 0, (
        f"UCI rows contain {n_nan_group} NaN `{GROUP_COLUMN}` values"
    )

    # Invariant 4 — unique student count
    n_unique = int(df[GROUP_COLUMN].nunique())
    assert n_unique == EXPECTED_UNIQUE_STUDENTS, (
        f"Expected {EXPECTED_UNIQUE_STUDENTS} unique students, got {n_unique}"
    )

    return df.reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════
# Feature matrix
# ═══════════════════════════════════════════════════════════════

def _fs_columns(fs: FeatureSet) -> tuple[list[str], list[str]]:
    """Return (numeric, categorical) columns for the requested feature set.

    Args:
        fs: "A" or "B".

    Returns:
        (numeric_columns, categorical_columns)

    Raises:
        ValueError: If `fs` is not in {"A", "B"}.
    """
    if fs == "A":
        return list(FS_A_NUMERIC), list(FS_A_CATEGORICAL)
    if fs == "B":
        return list(FS_B_NUMERIC), list(FS_B_CATEGORICAL)
    raise ValueError(f"Unknown feature set: {fs!r} (expected 'A' or 'B')")


def build_feature_matrix_v2(
    df: pd.DataFrame,
    fs: FeatureSet = "A",
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return (X, y, groups) for the requested feature set.

    X is *not* encoded — OneHotEncoder is applied per fold in pipeline_v2.

    Args:
        df: Output of `load_uci_only()`.
        fs: Feature set — "A" (demographic-only) or "B" (temporal + scores).

    Returns:
        X:      DataFrame with numeric + categorical features (raw, unencoded).
        y:      Series with target (`gpa`).
        groups: Series with `student_id` — pass to GroupKFold.split(X, y, groups).

    Raises:
        ValueError: If required columns are missing; if any excluded column
            appears in the feature set; or if NaN is present in X/y/groups.
    """
    numeric, categorical = _fs_columns(fs)
    required = set(numeric + categorical + [TARGET, GROUP_COLUMN])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Defensive — no leaky / zero-var / collinear / id / text column in FS
    forbidden_in_fs = set(numeric + categorical) & set(ALL_EXCLUDED)
    if forbidden_in_fs:
        raise ValueError(
            f"Feature set {fs!r} contains forbidden columns: "
            f"{sorted(forbidden_in_fs)}"
        )

    X = df[numeric + categorical].copy()
    y = df[TARGET].copy()
    groups = df[GROUP_COLUMN].copy()

    # Defensive — no NaN anywhere
    if X.isna().any().any():
        nulls = X.isna().sum()
        raise ValueError(
            f"X contains NaN values:\n{nulls[nulls > 0].to_string()}"
        )
    if y.isna().any():
        raise ValueError("Target `y` contains NaN values")
    if groups.isna().any():
        raise ValueError("`groups` contains NaN values")

    logger.info(
        "Feature matrix [FS-%s]: X.shape=%s, y.shape=%s, groups.nunique=%d",
        fs, X.shape, y.shape, groups.nunique(),
    )
    return X, y, groups


def get_feature_config_v2() -> dict:
    """Return feature configuration (used by tests & documentation)."""
    return {
        "target": TARGET,
        "group_column": GROUP_COLUMN,
        "fs_a": {
            "numeric": list(FS_A_NUMERIC),
            "categorical": list(FS_A_CATEGORICAL),
        },
        "fs_b": {
            "numeric": list(FS_B_NUMERIC),
            "categorical": list(FS_B_CATEGORICAL),
        },
        "excluded_leaky": list(EXCLUDED_LEAKY),
        "excluded_zero_var": list(EXCLUDED_ZERO_VAR),
        "excluded_collinear": list(EXCLUDED_COLLINEAR),
        "excluded_id": list(EXCLUDED_ID),
        "excluded_text": list(EXCLUDED_TEXT),
        "expected_uci_rows": EXPECTED_UCI_ROWS,
        "expected_unique_students": EXPECTED_UNIQUE_STUDENTS,
        "expected_multi_record_students": EXPECTED_MULTI_RECORD_STUDENTS,
    }


# ═══════════════════════════════════════════════════════════════
# CLI — Sanity check
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Sanity check: python -m src.ml.data_v2"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    df = load_uci_only()
    cfg = get_feature_config_v2()

    print()
    print("=" * 66)
    print("ML Data Layer v2 — Sanity Check")
    print("=" * 66)
    print(f"Rows (UCI-only):      {len(df):,}")
    print(f"Unique students:      {df[GROUP_COLUMN].nunique():,}")
    print(f"Columns in parquet:   {df.shape[1]}")
    print(f"Target:               {TARGET}")
    print(f"Target range:         [{df[TARGET].min():.4f}, {df[TARGET].max():.4f}]")
    print()

    for fs in ("A", "B"):
        X, y, groups = build_feature_matrix_v2(df, fs=fs)
        numeric, categorical = _fs_columns(fs)
        print(f"[FS-{fs}]")
        print(f"  numeric ({len(numeric)}):      {numeric}")
        print(f"  categorical ({len(categorical)}):  {categorical}")
        print(f"  X.shape:              {X.shape}")
        print(f"  y.shape:              {y.shape}")
        print(f"  groups.nunique:       {groups.nunique()}")
        print()

    print("Excluded columns (asserted absent from every FS):")
    for label, cols in [
        ("leaky",      cfg["excluded_leaky"]),
        ("zero-var",   cfg["excluded_zero_var"]),
        ("collinear",  cfg["excluded_collinear"]),
        ("id",         cfg["excluded_id"]),
        ("text",       cfg["excluded_text"]),
    ]:
        print(f"  {label:11s}: {cols}")


if __name__ == "__main__":
    main()