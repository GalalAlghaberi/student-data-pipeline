"""ML Data Layer — Phase B (Day 1).

Loads the Phase A feature store (ml_features.parquet), applies the
leakage audit from docs/ML_EXPERIMENTS.md §3, and returns (X, y).

**Leakage Audit (docs/ML_EXPERIMENTS.md §3):**
  Excluded (5 leaky columns):
    - avg_score           (gpa = avg_score / 25 — algebraic identity)
    - academic_risk_score (formula includes gpa)
    - performance_level   (derived from avg_score)
    - city_score_gap      (computed from avg_score)
    - city_rank           (ranked by avg_score)

  Excluded (2 ID/text):
    - student_id, full_name, date_of_birth

  Included (6 safe features — 4 numeric + 2 categorical):
    - attendance_rate     (numeric, [0, 1])
    - n_assessments       (numeric, count)
    - score_change        (numeric, temporal delta)
    - age                 (numeric, derived from date_of_birth)
    - gender, city        (categorical)

**Golden Rules:**
  - Add a layer; do not replace.
  - No changes to src/features/ or src/warehouse/.
  - Leakage prevention (Unit 9, pp. 76-77).
  - Deterministic (fixed REFERENCE_DATE).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR_DEFAULT = PROJECT_ROOT / "data" / "gold"
FEATURES_PARQUET = "ml_features.parquet"

# Fixed reference date for deterministic age computation.
# Changing this would change `age` values — keep frozen for reproducibility.
REFERENCE_DATE: Final = pd.Timestamp("2026-10-10")

# Target
TARGET: Final = "gpa"

# Safe features (post-leakage-audit)
FEATURES_NUMERIC: Final[list[str]] = [
    "attendance_rate",
    "n_assessments",
    "score_change",
    "age",
]
FEATURES_CATEGORICAL: Final[list[str]] = [
    "gender",
    "city",
]

# Excluded columns (documented for traceability & tests)
EXCLUDED_LEAKY: Final[list[str]] = [
    "avg_score",
    "academic_risk_score",
    "performance_level",
    "city_score_gap",
    "city_rank",
]
EXCLUDED_ID: Final[list[str]] = ["student_id"]
EXCLUDED_TEXT: Final[list[str]] = ["full_name", "date_of_birth"]


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def load_features(gold_dir: Path | str = GOLD_DIR_DEFAULT) -> pd.DataFrame:
    """Load ml_features.parquet and derive `age` from `date_of_birth`.

    Args:
        gold_dir: Directory containing ml_features.parquet.

    Returns:
        DataFrame with all original columns + derived `age`.

    Raises:
        FileNotFoundError: If ml_features.parquet is missing.
        ValueError: If `date_of_birth` column is missing.
    """
    gold_dir = Path(gold_dir)
    path = gold_dir / FEATURES_PARQUET
    if not path.exists():
        raise FileNotFoundError(
            f"Feature store not found: {path}\n"
            "Run: python -m src.features.engineering"
        )

    df = pd.read_parquet(path)
    logger.info(
        "Loaded features: shape=%s, columns=%d",
        df.shape, df.shape[1],
    )

    # Derive `age` deterministically from date_of_birth
    if "date_of_birth" not in df.columns:
        raise ValueError("`date_of_birth` column missing — cannot derive age")

    dob = pd.to_datetime(df["date_of_birth"], errors="coerce")
    if dob.isna().any():
        bad_rows = df.loc[dob.isna(), "student_id"].tolist() \
            if "student_id" in df.columns else "unknown"
        raise ValueError(
            f"Invalid date_of_birth values in rows: {bad_rows}"
        )

    age_days = (REFERENCE_DATE - dob).dt.days
    df["age"] = (age_days / 365.25).round().astype("Int64")
    logger.info(
        "Derived `age` from date_of_birth (ref=%s)",
        REFERENCE_DATE.date(),
    )

    return df


def build_feature_matrix(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) using only leakage-safe features.

    Args:
        df: Output of `load_features()`.

    Returns:
        X: DataFrame with numeric + categorical features.
        y: Series with target (`gpa`).

    Raises:
        ValueError: If required columns are missing or contain NaN.
    """
    required = set(FEATURES_NUMERIC + FEATURES_CATEGORICAL + [TARGET])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    X = df[FEATURES_NUMERIC + FEATURES_CATEGORICAL].copy()
    y = df[TARGET].copy()

    # Defensive: no NaN in features
    if X.isna().any().any():
        nulls = X.isna().sum()
        raise ValueError(
            f"X contains NaN values:\n{nulls[nulls > 0].to_string()}"
        )

    if y.isna().any():
        raise ValueError("Target `y` contains NaN values")

    logger.info(
        "Feature matrix: X.shape=%s, y.shape=%s",
        X.shape, y.shape,
    )
    return X, y


def get_feature_names() -> dict:
    """Return feature configuration (used by tests & documentation)."""
    return {
        "target": TARGET,
        "numeric": list(FEATURES_NUMERIC),
        "categorical": list(FEATURES_CATEGORICAL),
        "excluded_leaky": list(EXCLUDED_LEAKY),
        "excluded_id": list(EXCLUDED_ID),
        "excluded_text": list(EXCLUDED_TEXT),
        "reference_date": str(REFERENCE_DATE.date()),
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Sanity check: python -m src.ml.data"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    df = load_features()
    X, y = build_feature_matrix(df)

    print()
    print("=" * 60)
    print("ML Data Layer — Sanity Check")
    print("=" * 60)
    print(f"Rows:     {len(df)}")
    print(f"Features: {X.shape[1]} ({len(FEATURES_NUMERIC)} numeric + "
          f"{len(FEATURES_CATEGORICAL)} categorical)")
    print()
    print("X (feature matrix):")
    print(X.to_string(index=False))
    print()
    print("y (target):")
    print(y.to_string(index=False))
    print()
    print("Feature configuration:")
    for k, v in get_feature_names().items():
        print(f"  {k:18s}: {v}")


if __name__ == "__main__":
    main()