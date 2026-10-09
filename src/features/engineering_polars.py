"""Feature Engineering — Phase A (Polars Migration).

Parallel implementation of ``engineering.py`` (Pandas) using Polars.

**Contract (docs/POLARS_MIGRATION.md):**
  - MUST produce identical output to Pandas on the real dataset.
  - MUST NOT modify ``engineering.py`` or its tests.
  - MUST preserve Data Leakage Prevention (Unit 9, pp. 76-77).
  - MUST be idempotent (random_state=42).

**Golden Rules:**
  1. Add a layer; do not replace.
  2. All new code lives in src/features/.
  3. 162 v4.0.0 tests must remain green.
  4. Documentation before code (docs/POLARS_MIGRATION.md).

**Polars-specific design:**
  - Native Expressions: pl.col().filter().with_columns()
  - Window functions: .shift(1).over([...])
  - CASE WHEN: pl.when().then().otherwise()
  - Eager mode (pl.read_parquet) for 1:1 match with Pandas;
    lazy pipeline is demonstrated in scripts/benchmark_pandas_vs_polars.py.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration (mirror of engineering.py)
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR_DEFAULT = PROJECT_ROOT / "data" / "gold"
CSV_FALLBACK = PROJECT_ROOT / "data" / "processed" / "csv" / "csv_clean.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2

PERFORMANCE_BINS: list[tuple[float, str]] = [
    (90.0, "Excellent"),
    (80.0, "Very Good"),
    (70.0, "Good"),
    (60.0, "Pass"),
    (-np.inf, "Weak"),
]

GOLD_TABLES: dict[str, str] = {
    "dim_students": "dim_students.parquet",
    "dim_courses": "dim_courses.parquet",
    "dim_instructors": "dim_instructors.parquet",
    "dim_time": "dim_time.parquet",
    "fact_student_performance": "fact_student_performance.parquet",
    "fact_enrollment": "fact_enrollment.parquet",
}


# ═══════════════════════════════════════════════════════════════
# Feature Catalog (mirror)
# ═══════════════════════════════════════════════════════════════

@dataclass
class FeatureSpec:
    name: str
    formula: str
    source: str
    leakage_risk: str = "none"
    range_min: float | None = None
    range_max: float | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FEATURE_CATALOG: dict[str, FeatureSpec] = {
    "attendance_rate": FeatureSpec(
        name="attendance_rate",
        formula="attendance / 100",
        source="Unit 6, p. 37",
        leakage_risk="none",
        range_min=0.0, range_max=1.0,
        description="Normalized attendance on a 0-1 scale.",
    ),
    "academic_risk_score": FeatureSpec(
        name="academic_risk_score",
        formula="(4 - gpa) + ((100 - attendance) / 25)",
        source="Unit 6, p. 51",
        leakage_risk="none",
        range_min=0.0, range_max=10.0,
        description="Higher value indicates higher academic risk.",
    ),
    "score_change": FeatureSpec(
        name="score_change",
        formula=(
            "score - LAG(score) OVER ("
            "PARTITION BY student_id, course_id ORDER BY assessment_id)"
        ),
        source="Unit 3, pp. 36-38",
        leakage_risk="none",
        description="Mean of consecutive assessment deltas per student.",
    ),
    "city_rank": FeatureSpec(
        name="city_rank",
        formula=(
            "1 + count(TRAIN peers with strictly higher avg_score "
            "in same city)"
        ),
        source="Unit 3, p. 33",
        leakage_risk="high",
        description=(
            "Position within city, computed from TRAIN peers only "
            "(Unit 9, pp. 76-77)."
        ),
    ),
    "city_score_gap": FeatureSpec(
        name="city_score_gap",
        formula="avg_score - median(avg_score of same city in TRAIN)",
        source="Design — derived from Unit 3, p. 33",
        leakage_risk="low",
        description=(
            "Signed gap between student's avg_score and their city's "
            "TRAIN median."
        ),
    ),
    "performance_level": FeatureSpec(
        name="performance_level",
        formula="CASE WHEN avg_score >= 90 THEN 'Excellent' ... END",
        source="Unit 3, p. 19",
        leakage_risk="none",
        description="Categorical performance classification.",
    ),
}


# ═══════════════════════════════════════════════════════════════
# Exceptions (mirror)
# ═══════════════════════════════════════════════════════════════

class FeatureEngineeringError(RuntimeError):
    """Raised when feature engineering fails."""


class SchemaMismatchError(FeatureEngineeringError):
    """Raised when a Gold table lacks required columns."""


# ═══════════════════════════════════════════════════════════════
# PolarsFeatureEngineer
# ═══════════════════════════════════════════════════════════════

class PolarsFeatureEngineer:
    """Polars equivalent of FeatureEngineer.

    Guarantees:
      - Same output as Pandas on the real dataset (8 rows).
      - Deterministic split (NumPy RNG with random_state=42).
      - Data Leakage Prevention preserved (Unit 9, pp. 76-77).
    """

    def __init__(
        self,
        gold_dir: Path | str = GOLD_DIR_DEFAULT,
        test_size: float = TEST_SIZE,
        random_state: int = RANDOM_STATE,
    ) -> None:
        self.gold_dir = Path(gold_dir)
        self.test_size = test_size
        self.random_state = random_state

        self.tables: dict[str, pl.DataFrame] = {}
        self._features: pl.DataFrame | None = None
        self._train: pl.DataFrame | None = None
        self._test: pl.DataFrame | None = None
        self._train_stats: dict[str, float] = {}

    # ───────────────────────────────────────────────────────────
    # 1. Load Gold
    # ───────────────────────────────────────────────────────────

    def load_gold(self) -> None:
        """Load all 6 Gold tables (eager, mirrors Pandas behaviour)."""
        if not self.gold_dir.exists():
            raise FeatureEngineeringError(
                f"Gold directory not found: {self.gold_dir}"
            )
        for name, fname in GOLD_TABLES.items():
            path = self.gold_dir / fname
            if not path.exists():
                raise FeatureEngineeringError(
                    f"Missing Gold table: {path}. "
                    "Run: python -m src.warehouse.star_schema"
                )
            # Eager read (mirrors pd.read_parquet for 1:1 semantic match)
            df = pl.read_parquet(path)
            self.tables[name] = df
            logger.info(
                "Loaded %-28s shape=%s cols=%s",
                name, (df.height, df.width), df.columns,
            )

    # ───────────────────────────────────────────────────────────
    # 2. Build Base Features (row-wise, no statistics)
    # ───────────────────────────────────────────────────────────

    def build_base_features(self) -> pl.DataFrame:
        """Build one row per student with leak-free, row-wise features."""
        self._require_tables("dim_students", "fact_student_performance")
        students = self.tables["dim_students"]
        perf = self.tables["fact_student_performance"]

        self._require_columns(students, {"student_id"}, "dim_students")
        self._require_columns(perf, {"student_id"}, "fact_student_performance")

        # ─── GPA ────────────────────────────────────────────────
        if "gpa" in students.columns:
            students = students.with_columns(
                pl.col("gpa").cast(pl.Float64, strict=False)
            )
            logger.info("GPA: using dim_students.gpa column.")
        else:
            if "score" not in perf.columns:
                raise SchemaMismatchError(
                    "Cannot derive gpa: no 'gpa' in dim_students and "
                    "no 'score' in fact_student_performance."
                )
            derived = (
                perf.group_by("student_id")
                .agg((pl.col("score").mean() / 25.0).alias("gpa"))
            )
            students = students.join(derived, on="student_id", how="left")
            students = students.with_columns(
                pl.col("gpa").round(3)
            )
            logger.info(
                "GPA: derived from fact_student_performance "
                "(mean score / 25)."
            )

        # ─── Attendance (multi-source fallback) ─────────────────
        attendance_series = self._resolve_attendance(students, perf)
        students = students.with_columns(
            attendance_series.alias("attendance")
        )

        # ─── avg_score, n_assessments ──────────────────────────
        if "score" not in perf.columns:
            raise SchemaMismatchError(
                "fact_student_performance must have 'score' column."
            )
        agg = perf.group_by("student_id").agg(
            pl.col("score").mean().alias("avg_score"),
            pl.col("score").len().alias("n_assessments"),
        )

        # ─── score_change ───────────────────────────────────────
        score_change = self._compute_score_change(perf)
        agg = agg.join(score_change, on="student_id", how="left")
        agg = agg.with_columns(
            pl.col("score_change").fill_null(0.0)
        )

        # ─── Merge ──────────────────────────────────────────────
        features = students.join(agg, on="student_id", how="left")

        # ─── Derived (row-wise, leak-free) ──────────────────────
        features = features.with_columns([
            (pl.col("attendance") / 100.0).round(4).alias("attendance_rate"),
            (
                (4.0 - pl.col("gpa"))
                + ((100.0 - pl.col("attendance")) / 25.0)
            ).round(4).alias("academic_risk_score"),
        ])
        features = features.with_columns(
            self._classify_performance_expr().alias("performance_level")
        )

        # ─── Reorder (mirror Pandas 'preferred + rest') ─────────
        preferred = [
            "student_id", "gpa", "attendance", "avg_score",
            "n_assessments", "score_change", "attendance_rate",
            "academic_risk_score", "performance_level",
        ]
        rest = [c for c in features.columns if c not in preferred]
        features = features.select(preferred + rest)

        self._features = features
        logger.info(
            "Base features built: shape=%s grain=1 student",
            (features.height, features.width),
        )
        return features

    # ───────────────────────────────────────────────────────────
    # 3. Split
    # ───────────────────────────────────────────────────────────

    def split_train_test(self) -> None:
        """Deterministic split — uses NumPy RNG for byte-identical
        permutation with the Pandas implementation."""
        if self._features is None:
            raise FeatureEngineeringError(
                "Call build_base_features() first."
            )
        n = self._features.height
        n_test = max(1, int(round(n * self.test_size)))
        n_train = n - n_test

        rng = np.random.default_rng(self.random_state)
        indices = rng.permutation(n)

        # Positional row selection (mirror .iloc[indices[...]])
        train_idx = indices[:n_train].tolist()
        test_idx = indices[n_train:].tolist()

        self._train = self._features[train_idx].with_columns(
            pl.lit("train").alias("split")
        )
        self._test = self._features[test_idx].with_columns(
            pl.lit("test").alias("split")
        )

        logger.info(
            "Split: train=%d test=%d (seed=%d)",
            self._train.height, self._test.height, self.random_state,
        )

    # ───────────────────────────────────────────────────────────
    # 4. Stats (TRAIN ONLY)
    # ───────────────────────────────────────────────────────────

    def compute_train_statistics(self) -> dict[str, float]:
        """Compute imputation stats from TRAIN only (Unit 9, pp. 76-77)."""
        if self._train is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        def _median(df: pl.DataFrame, col: str) -> float:
            val = df.select(pl.col(col).median()).item()
            return float(val) if val is not None else 0.0

        self._train_stats = {
            "gpa_median": _median(self._train, "gpa"),
            "attendance_median": _median(self._train, "attendance"),
            "avg_score_median": _median(self._train, "avg_score"),
        }
        logger.info("Train statistics: %s", self._train_stats)
        return self._train_stats

    # ───────────────────────────────────────────────────────────
    # 5. Apply Stats (TRAIN + TEST)
    # ───────────────────────────────────────────────────────────

    def apply_statistics(self) -> None:
        """Apply TRAIN statistics to both TRAIN and TEST."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")
        if not self._train_stats:
            raise FeatureEngineeringError(
                "Call compute_train_statistics() first."
            )

        fill_map = {
            "gpa": self._train_stats["gpa_median"],
            "attendance": self._train_stats["attendance_median"],
            "avg_score": self._train_stats["avg_score_median"],
        }

        def _impute(df: pl.DataFrame) -> pl.DataFrame:
            for col, val in fill_map.items():
                n_missing = df[col].is_null().sum()
                df = df.with_columns(
                    pl.col(col).fill_null(val)
                )
                if n_missing:
                    logger.info(
                        "Imputed %s: n=%d value=%.4f", col, n_missing, val
                    )
            # Recompute derived features after imputation
            df = df.with_columns([
                (pl.col("attendance") / 100.0).round(4).alias("attendance_rate"),
                (
                    (4.0 - pl.col("gpa"))
                    + ((100.0 - pl.col("attendance")) / 25.0)
                ).round(4).alias("academic_risk_score"),
            ])
            df = df.with_columns(
                self._classify_performance_expr().alias("performance_level")
            )
            return df

        self._train = _impute(self._train)
        self._test = _impute(self._test)

    # ───────────────────────────────────────────────────────────
    # 6. City Features (TRAIN ONLY — after split)
    # ───────────────────────────────────────────────────────────

    def compute_city_rank(self) -> None:
        """Compute city_rank and city_score_gap using TRAIN-only stats."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        if "city" not in self._train.columns:
            logger.warning(
                "No 'city' column — city_rank/city_score_gap set to null."
            )
            for name in ("_train", "_test"):
                df = getattr(self, name)
                df = df.with_columns([
                    pl.lit(None, dtype=pl.Int64).alias("city_rank"),
                    pl.lit(None, dtype=pl.Float64).alias("city_score_gap"),
                ])
                setattr(self, name, df)
            return

        # ─── TRAIN-only reference statistics ────────────────────
        train_valid = self._train.filter(
            pl.col("city").is_not_null() & pl.col("avg_score").is_not_null()
        )

        # city → median
        train_city_median: dict[str, float] = {
            row["city"]: float(row["avg_score_median"])
            for row in train_valid.group_by("city").agg(
                pl.col("avg_score").median().alias("avg_score_median")
            ).iter_rows(named=True)
        }

        # city → sorted descending list of TRAIN avg_scores
        train_city_scores: dict[str, list[float]] = {}
        for row in train_valid.select(["city", "avg_score"]).iter_rows(named=True):
            train_city_scores.setdefault(row["city"], []).append(row["avg_score"])
        for city in train_city_scores:
            train_city_scores[city].sort(reverse=True)

        # Fallback median (TRAIN global)
        fallback_median = (
            float(train_valid["avg_score"].median())
            if train_valid.height > 0 else 0.0
        )

        # ─── Apply ──────────────────────────────────────────────
        def _gap(city: Any, avg: Any) -> float:
            if city is None or avg is None:
                return 0.0
            ref = train_city_median.get(city, fallback_median)
            return round(float(avg - ref), 4)

        def _rank(city: Any, avg: Any) -> Any:
            if city is None or avg is None:
                return None
            scores = train_city_scores.get(city)
            if not scores:
                return None
            return 1 + sum(1 for s in scores if s > avg)

        def _add_city_cols(df: pl.DataFrame) -> pl.DataFrame:
            cities = df["city"].to_list()
            avgs = df["avg_score"].to_list()
            gaps = [_gap(c, a) for c, a in zip(cities, avgs)]
            ranks = [_rank(c, a) for c, a in zip(cities, avgs)]
            return df.with_columns([
                pl.Series("city_score_gap", gaps, dtype=pl.Float64),
                pl.Series("city_rank", ranks, dtype=pl.Int64),
            ])

        self._train = _add_city_cols(self._train)
        self._test = _add_city_cols(self._test)

        logger.info(
            "City features computed from TRAIN-only stats: %d cities, "
            "fallback_median=%.4f",
            len(train_city_median), fallback_median,
        )

    # ───────────────────────────────────────────────────────────
    # 7. Validate
    # ───────────────────────────────────────────────────────────

    def validate(self) -> None:
        """Run quality checks; raise on failure."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        full = pl.concat([self._train, self._test], how="vertical")

        # ─── Grain ──────────────────────────────────────────────
        if full["student_id"].n_unique() != full.height:
            raise FeatureEngineeringError(
                "student_id must be unique (grain = 1 student)."
            )

        # ─── No null in critical features ───────────────────────
        critical = [
            "attendance_rate", "academic_risk_score",
            "performance_level", "avg_score", "gpa",
        ]
        for col in critical:
            if full[col].is_null().any():
                raise FeatureEngineeringError(
                    f"Column '{col}' contains null after imputation."
                )

        # ─── Ranges ─────────────────────────────────────────────
        if not full["attendance_rate"].is_between(0.0, 1.0).all():
            raise FeatureEngineeringError("attendance_rate out of [0, 1].")
        if not full["gpa"].is_between(0.0, 4.0).all():
            raise FeatureEngineeringError("gpa out of [0, 4].")

        # ─── Categories ─────────────────────────────────────────
        allowed = {label for _, label in PERFORMANCE_BINS}
        observed = set(full["performance_level"].unique().to_list())
        unknown = observed - allowed
        if unknown:
            raise FeatureEngineeringError(
                f"Unknown performance_level values: {unknown}"
            )

        # ─── Split column ───────────────────────────────────────
        if set(full["split"].unique().to_list()) != {"train", "test"}:
            raise FeatureEngineeringError(
                "split column must contain only {train, test}."
            )

        logger.info("Validation passed for %d students.", full.height)

    # ───────────────────────────────────────────────────────────
    # 8. Save
    # ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist features, metadata, and split (mirrors Pandas)."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError(
                "Nothing to save — call split_train_test() first."
            )

        full = pl.concat([self._train, self._test], how="vertical")
        full = full.sort("student_id")

        features_path = self.gold_dir / "ml_features_polars.parquet"
        split_path = self.gold_dir / "train_test_split_polars.parquet"
        metadata_path = self.gold_dir / "feature_metadata_polars.json"

        full.drop("split").write_parquet(features_path)
        full.select(["student_id", "split"]).write_parquet(split_path)

        metadata = {
            "version": "v4.1.0-dev",
            "phase": "A (Polars Migration)",
            "grain": "1 student",
            "n_rows": int(full.height),
            "n_train": int((full["split"] == "train").sum()),
            "n_test": int((full["split"] == "test").sum()),
            "random_state": self.random_state,
            "test_size": self.test_size,
            "train_statistics": self._train_stats,
            "features": {
                k: v.to_dict() for k, v in FEATURE_CATALOG.items()
            },
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("Saved: %s", features_path)
        logger.info("Saved: %s", split_path)
        logger.info("Saved: %s", metadata_path)

    # ───────────────────────────────────────────────────────────
    # Orchestration
    # ───────────────────────────────────────────────────────────

    def run(self) -> pl.DataFrame:
        """Run the full pipeline end-to-end."""
        logger.info("=" * 60)
        logger.info("Feature Engineering — Phase A (Polars, v4.1.0-dev)")
        logger.info("=" * 60)

        self.load_gold()
        self.build_base_features()
        self.split_train_test()
        self.compute_train_statistics()
        self.apply_statistics()
        self.compute_city_rank()
        self.validate()
        self.save()

        logger.info("=" * 60)
        logger.info("DONE. ml_features_polars.parquet written.")
        logger.info("=" * 60)

        return (
            pl.concat([self._train, self._test], how="vertical")
            .sort("student_id")
        )

    # ───────────────────────────────────────────────────────────
    # Private helpers
    # ───────────────────────────────────────────────────────────

    def _require_tables(self, *names: str) -> None:
        missing = [n for n in names if n not in self.tables]
        if missing:
            raise FeatureEngineeringError(
                f"Tables not loaded: {missing}. Call load_gold() first."
            )

    @staticmethod
    def _require_columns(
        df: pl.DataFrame, cols: set[str], table: str
    ) -> None:
        missing = cols - set(df.columns)
        if missing:
            raise SchemaMismatchError(
                f"Table '{table}' missing columns: {sorted(missing)}. "
                f"Available: {sorted(df.columns)}"
            )

    @staticmethod
    def _classify_performance_expr() -> pl.Expr:
        """Polars-native CASE WHEN for performance_level.

        Mirrors _classify_performance (NaN → 'Weak'; first matching bin).
        """
        expr = pl.when(pl.col("avg_score").is_null()).then(pl.lit("Weak"))
        for threshold, label in PERFORMANCE_BINS:
            if threshold == -np.inf:
                break
            expr = expr.when(pl.col("avg_score") >= threshold).then(
                pl.lit(label)
            )
        return expr.otherwise(pl.lit("Weak"))

    @staticmethod
    def _resolve_attendance(
        students: pl.DataFrame, perf: pl.DataFrame
    ) -> pl.Series:
        """Resolve attendance from multiple sources (mirror Pandas)."""
        # Source 1: dim_students.attendance
        if "attendance" in students.columns:
            series = students["attendance"].cast(pl.Float64, strict=False)
            if series.is_not_null().any():
                logger.info("Attendance: from dim_students.attendance.")
                return series

        # Source 2: fact_student_performance.attendance
        if "attendance" in perf.columns:
            agg = perf.group_by("student_id").agg(
                pl.col("attendance").mean().alias("attendance")
            )
            joined = students.select("student_id").join(
                agg, on="student_id", how="left"
            )
            series = joined["attendance"]
            if series.is_not_null().any():
                logger.info(
                    "Attendance: from fact_student_performance.attendance."
                )
                return series

        # Source 3: CSV pipeline
        if CSV_FALLBACK.exists():
            try:
                csv_df = pl.read_csv(CSV_FALLBACK)
                if {"student_id", "attendance"}.issubset(set(csv_df.columns)):
                    csv_df = csv_df.with_columns(
                        pl.col("attendance").cast(pl.Float64, strict=False)
                    ).select(["student_id", "attendance"])
                    joined = students.select("student_id").join(
                        csv_df, on="student_id", how="left"
                    )
                    series = joined["attendance"]
                    if series.is_not_null().any():
                        logger.info(
                            "Attendance: from %s (CSV pipeline).",
                            CSV_FALLBACK.name,
                        )
                        return series
                else:
                    logger.warning(
                        "CSV lacks required columns: %s", csv_df.columns
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to read %s: %s", CSV_FALLBACK, exc)

        # Fallback
        logger.warning(
            "No attendance source found; defaulting to 100.0. "
            "attendance_rate will be constant 1.0."
        )
        return pl.Series(
            "attendance",
            [100.0] * students.height,
            dtype=pl.Float64,
        )

    @staticmethod
    def _compute_score_change(perf: pl.DataFrame) -> pl.DataFrame:
        """Mean of consecutive score deltas per student (mirror Pandas)."""
        # Determine order column
        order_col = None
        for cand in ("assessment_id", "id"):
            if cand in perf.columns:
                order_col = cand
                break
        if order_col is None:
            # Add positional row index
            perf = perf.with_row_index("_row_id")
            order_col = "_row_id"

        group_cols = ["student_id"]
        if "course_id" in perf.columns:
            group_cols.append("course_id")

        df = perf.sort(group_cols + [order_col])

        # LAG via .shift(1).over(group_cols)
        df = df.with_columns(
            (
                pl.col("score")
                - pl.col("score").shift(1).over(group_cols)
            ).alias("_delta")
        )

        # Drop nulls (first row per group) and average per student
        return (
            df.filter(pl.col("_delta").is_not_null())
            .group_by("student_id")
            .agg(pl.col("_delta").mean().alias("score_change"))
        )


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # ASCII-safe table formatting (Windows charmap compatibility)
    pl.Config.set_tbl_formatting("ASCII_MARKDOWN")

    engineer = PolarsFeatureEngineer()
    df = engineer.run()
    print()
    print("=" * 60)
    print("Preview: ml_features_polars.parquet")
    print("=" * 60)
    print(df)


if __name__ == "__main__":
    main()