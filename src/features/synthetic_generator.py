"""
Synthetic Data Generator — Phase A (Polars Migration).

Generates schema-valid synthetic student data at scale (100K / 1M rows)
for benchmarking Pandas vs Polars. The real dataset has only 8 rows.

Reference:
    - docs/POLARS_MIGRATION.md §7
    - Unit 6 (p. 60, Scalability Wall)
    - Guide Ch 5 (Compute & Resources)

Golden Rules:
    - Add a layer, do not replace (Pandas pipeline untouched)
    - Reproducible (seed=42)
    - Schema-valid (all constraints enforced before return)
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import polars as pl

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

__all__ = ["generate_synthetic"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DIM_STUDENTS_PARQUET = PROJECT_ROOT / "data" / "gold" / "dim_students.parquet"
SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"

DEFAULT_SEED = 42
FALLBACK_CITIES = ["Sanaa", "Dhamar", "Ibb", "Taiz"]
AGE_RANGE = (16, 80)
GPA_RANGE = (0.0, 4.0)
ATTENDANCE_RANGE = (0.0, 100.0)
GENDERS = ["Male", "Female"]
N_ASSESSMENTS_CHOICES = [2, 4]


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def generate_synthetic(
    n_rows: int,
    *,
    seed: int = DEFAULT_SEED,
    real_cities: list[str] | None = None,
    output_path: Path | None = None,
) -> pl.DataFrame:
    """Generate schema-valid synthetic student data.

    Args:
        n_rows: Number of student records.
        seed: RNG seed for reproducibility.
        real_cities: Cities from dim_students.parquet. Auto-loaded if None.
        output_path: Optional parquet path. If set, writes and returns DataFrame.

    Returns:
        Polars DataFrame with columns:
            student_id, name, city, age, gender,
            gpa, attendance, n_assessments.

    Guarantees:
        - student_id unique and monotonic (1001, 1002, ...)
        - age ∈ [16, 80]
        - gpa ∈ [0.0, 4.0]
        - attendance ∈ [0.0, 100.0]
        - gender ∈ {"Male", "Female"}
        - city ∈ real_cities
        - n_assessments ∈ {2, 4}
        - Deterministic for fixed seed
    """
    if n_rows < 1:
        raise ValueError(f"n_rows must be >= 1, got {n_rows}")

    if real_cities is None:
        real_cities = _load_real_cities()
    real_cities = sorted(set(real_cities))
    if not real_cities:
        raise ValueError("real_cities cannot be empty")

    rng = np.random.default_rng(seed=seed)
    logger.info(
        "Generating %d synthetic rows (seed=%d, cities=%d)",
        n_rows, seed, len(real_cities),
    )

    # ── Primitive arrays (NumPy for speed + determinism) ──
    student_id = np.arange(1001, 1001 + n_rows, dtype=np.int64)

    city_arr = np.array(real_cities, dtype=object)
    city = city_arr[rng.integers(0, len(real_cities), size=n_rows)]

    age = rng.integers(
        AGE_RANGE[0], AGE_RANGE[1] + 1, size=n_rows, dtype=np.int64
    )

    gender_arr = np.array(GENDERS, dtype=object)
    gender = gender_arr[rng.integers(0, len(GENDERS), size=n_rows)]

    gpa = rng.uniform(GPA_RANGE[0], GPA_RANGE[1], size=n_rows).round(2)

    attendance = rng.uniform(
        ATTENDANCE_RANGE[0], ATTENDANCE_RANGE[1], size=n_rows
    ).round(1)

    n_assessments = rng.choice(N_ASSESSMENTS_CHOICES, size=n_rows).astype(np.int64)

    name = np.array(
        [f"Synthetic Student {sid:06d}" for sid in student_id],
        dtype=object,
    )

    # ── Assemble Polars DataFrame with explicit schema ──
    df = pl.DataFrame(
        {
            "student_id": student_id,
            "name": name,
            "city": city,
            "age": age,
            "gender": gender,
            "gpa": gpa,
            "attendance": attendance,
            "n_assessments": n_assessments,
        },
        schema={
            "student_id": pl.Int64,
            "name": pl.Utf8,
            "city": pl.Utf8,
            "age": pl.Int64,
            "gender": pl.Utf8,
            "gpa": pl.Float64,
            "attendance": pl.Float64,
            "n_assessments": pl.Int64,
        },
    )

    # ── Defense in depth ──
    _validate_synthetic(df, real_cities)

    logger.info("Generated %d rows × %d columns", df.height, df.width)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(output_path)
        logger.info("Wrote synthetic data to %s", output_path)

    return df


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _load_real_cities() -> list[str]:
    """Load real cities from dim_students.parquet, or fallback."""
    if DIM_STUDENTS_PARQUET.exists():
        try:
            df = pl.read_parquet(DIM_STUDENTS_PARQUET)
            cities = df["city"].unique().sort().to_list()
            logger.info("Loaded %d real cities from Gold layer", len(cities))
            return cities
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load dim_students (%s). Using fallback.", exc)

    logger.info("dim_students.parquet missing. Using fallback cities.")
    return list(FALLBACK_CITIES)


def _validate_synthetic(df: pl.DataFrame, allowed_cities: list[str]) -> None:
    """Enforce schema contract; raise ValueError on any violation."""
    if df["student_id"].n_unique() != df.height:
        raise ValueError("student_id must be unique")

    if not df["age"].is_between(*AGE_RANGE).all():
        raise ValueError(f"age must be in {AGE_RANGE}")

    if not df["gpa"].is_between(*GPA_RANGE).all():
        raise ValueError(f"gpa must be in {GPA_RANGE}")

    if not df["attendance"].is_between(*ATTENDANCE_RANGE).all():
        raise ValueError(f"attendance must be in {ATTENDANCE_RANGE}")

    if set(df["gender"].unique().to_list()) - set(GENDERS):
        raise ValueError(
            f"invalid gender values: {df['gender'].unique().to_list()}"
        )

    if set(df["city"].unique().to_list()) - set(allowed_cities):
        raise ValueError(
            f"invalid city values: {df['city'].unique().to_list()}"
        )

    if set(df["n_assessments"].unique().to_list()) - set(N_ASSESSMENTS_CHOICES):
        raise ValueError(
            f"invalid n_assessments: {df['n_assessments'].unique().to_list()}"
        )

    if df.null_count().sum_horizontal().item() > 0:
        raise ValueError("synthetic data contains nulls")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """CLI: python -m src.features.synthetic_generator --size 100000"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Generate schema-valid synthetic student data for benchmarking."
    )
    parser.add_argument(
        "--size", type=int, required=True,
        help="Number of rows (e.g., 100000, 1000000)",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"RNG seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output path (default: data/synthetic/students_{size}.parquet)",
    )
    args = parser.parse_args()

    output = args.output or (SYNTHETIC_DIR / f"students_{args.size}.parquet")
    df = generate_synthetic(
        n_rows=args.size, seed=args.seed, output_path=output
    )

    print(f"\n✅ Generated {df.height:,} rows × {df.width} columns")
    print(f"   Output: {output}")
    print(f"\n   Sample (head 3):")
    print(df.head(3))


if __name__ == "__main__":
    main()