"""Feature Engineering — Phase A.

Builds an ML-ready feature store from the Gold (Star Schema) layer.

**Golden Rules (docs/FEATURE_STORE.md):**
  1. Add a layer; do not replace existing layers.
  2. All new code lives in src/features/ — no changes to src/warehouse/.
  3. All 140 v3.0.0 tests must remain green.
  4. Documentation before code.

**Leakage Prevention (Unit 9, pp. 76-77):**
  - Split TRAIN/TEST first.
  - Compute statistics (median, mean, city rank) from TRAIN ONLY.
  - Apply TRAIN statistics to both TRAIN and TEST.

**Design notes:**
  - `city_rank` is computed AFTER split using TRAIN peers only.
  - `city_score_gap` (numerical) replaces `city_rank` as the primary
    city-level feature for ML, since ranks are unstable with small N.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR_DEFAULT = PROJECT_ROOT / "data" / "gold"
CSV_FALLBACK = PROJECT_ROOT / "data" / "processed" / "csv" / "csv_clean.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Performance classification thresholds (Unit 3, p. 19)
PERFORMANCE_BINS: list[tuple[float, str]] = [
    (90.0, "Excellent"),
    (80.0, "Very Good"),
    (70.0, "Good"),
    (60.0, "Pass"),
    (-np.inf, "Weak"),
]

# Expected Gold tables (name → filename)
GOLD_TABLES: dict[str, str] = {
    "dim_students": "dim_students.parquet",
    "dim_courses": "dim_courses.parquet",
    "dim_instructors": "dim_instructors.parquet",
    "dim_time": "dim_time.parquet",
    "fact_student_performance": "fact_student_performance.parquet",
    "fact_enrollment": "fact_enrollment.parquet",
}


# ═══════════════════════════════════════════════════════════════
# Feature Catalog (Metadata)
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
        range_min=0.0,
        range_max=1.0,
        description="Normalized attendance on a 0-1 scale.",
    ),
    "academic_risk_score": FeatureSpec(
        name="academic_risk_score",
        formula="(4 - gpa) + ((100 - attendance) / 25)",
        source="Unit 6, p. 51",
        leakage_risk="none",
        range_min=0.0,
        range_max=10.0,
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
            "RANK() OVER (PARTITION BY city ORDER BY avg_score DESC), "
            "using TRAIN peers only"
        ),
        source="Unit 3, p. 33",
        leakage_risk="high",
        description=(
            "Position within city, computed from TRAIN peers only "
            "(Unit 9, pp. 76-77). Test students are ranked against "
            "TRAIN thresholds."
        ),
    ),
    "city_score_gap": FeatureSpec(
        name="city_score_gap",
        formula="avg_score - median(avg_score of same city in TRAIN)",
        source="Design — derived from Unit 3, p. 33",
        leakage_risk="low",
        description=(
            "Signed gap between student's avg_score and their city's "
            "TRAIN median. Zero for the median student; positive for "
            "above-median students."
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
# Exceptions
# ═══════════════════════════════════════════════════════════════

class FeatureEngineeringError(RuntimeError):
    """Raised when feature engineering fails."""


class SchemaMismatchError(FeatureEngineeringError):
    """Raised when a Gold table lacks required columns."""


# ═══════════════════════════════════════════════════════════════
# FeatureEngineer
# ═══════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Build an ML-ready feature store with leakage prevention."""

    def __init__(
        self,
        gold_dir: Path | str = GOLD_DIR_DEFAULT,
        test_size: float = TEST_SIZE,
        random_state: int = RANDOM_STATE,
    ) -> None:
        self.gold_dir = Path(gold_dir)
        self.test_size = test_size
        self.random_state = random_state

        self.tables: dict[str, pd.DataFrame] = {}
        self._features: pd.DataFrame | None = None
        self._train: pd.DataFrame | None = None
        self._test: pd.DataFrame | None = None
        self._train_stats: dict[str, float] = {}

    # ───────────────────────────────────────────────────────────
    # 1. Load Gold
    # ───────────────────────────────────────────────────────────

    def load_gold(self) -> None:
        """Load all 6 Gold tables; fail clearly if any is missing."""
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
            df = pd.read_parquet(path)
            self.tables[name] = df
            logger.info(
                "Loaded %-28s shape=%s cols=%s",
                name, df.shape, list(df.columns),
            )

    # ───────────────────────────────────────────────────────────
    # 2. Build Base Features (row-wise, no statistics)
    # ───────────────────────────────────────────────────────────

    def build_base_features(self) -> pd.DataFrame:
        """Build one row per student with leak-free, row-wise features.

        Does NOT compute any feature that depends on the peer distribution
        (e.g., city_rank) — those go to compute_city_rank() AFTER split.
        """
        self._require_tables("dim_students", "fact_student_performance")
        students = self.tables["dim_students"].copy()
        perf = self.tables["fact_student_performance"].copy()

        self._require_columns(students, {"student_id"}, "dim_students")
        self._require_columns(perf, {"student_id"}, "fact_student_performance")

        # ─── GPA ────────────────────────────────────────────────
        if "gpa" in students.columns:
            students["gpa"] = pd.to_numeric(
                students["gpa"], errors="coerce"
            )
            logger.info("GPA: using dim_students.gpa column.")
        else:
            if "score" not in perf.columns:
                raise SchemaMismatchError(
                    "Cannot derive gpa: no 'gpa' in dim_students and "
                    "no 'score' in fact_student_performance."
                )
            derived = perf.groupby("student_id")["score"].mean() / 25.0
            students["gpa"] = (
                students["student_id"].map(derived).astype(float).round(3)
            )
            logger.info(
                "GPA: derived from fact_student_performance "
                "(mean score / 25)."
            )

        # ─── Attendance (multi-source fallback) ─────────────────
        students["attendance"] = self._resolve_attendance(students, perf)

        # ─── avg_score, n_assessments ──────────────────────────
        if "score" not in perf.columns:
            raise SchemaMismatchError(
                "fact_student_performance must have 'score' column."
            )
        agg = (
            perf.groupby("student_id", as_index=False)
            .agg(
                avg_score=("score", "mean"),
                n_assessments=("score", "size"),
            )
        )

        # ─── score_change ───────────────────────────────────────
        score_change = self._compute_score_change(perf)
        agg = agg.merge(score_change, on="student_id", how="left")
        agg["score_change"] = agg["score_change"].fillna(0.0)

        # ─── Merge ──────────────────────────────────────────────
        features = students.merge(agg, on="student_id", how="left")

        # ─── Derived (row-wise, leak-free) ──────────────────────
        features["attendance_rate"] = (
            features["attendance"] / 100.0
        ).round(4)
        features["academic_risk_score"] = (
            (4.0 - features["gpa"])
            + ((100.0 - features["attendance"]) / 25.0)
        ).round(4)
        features["performance_level"] = features["avg_score"].apply(
            self._classify_performance
        )

        # ─── Reorder ────────────────────────────────────────────
        preferred = [
            "student_id", "gpa", "attendance", "avg_score",
            "n_assessments", "score_change", "attendance_rate",
            "academic_risk_score", "performance_level",
        ]
        rest = [c for c in features.columns if c not in preferred]
        features = features[preferred + rest]

        self._features = features
        logger.info(
            "Base features built: shape=%s grain=1 student", features.shape
        )
        return features

    # ───────────────────────────────────────────────────────────
    # 3. Split
    # ───────────────────────────────────────────────────────────

    def split_train_test(self) -> None:
        """Deterministic split. Simple shuffle (N=8 too small for stratify)."""
        if self._features is None:
            raise FeatureEngineeringError(
                "Call build_base_features() first."
            )
        n = len(self._features)
        n_test = max(1, int(round(n * self.test_size)))
        n_train = n - n_test

        rng = np.random.default_rng(self.random_state)
        indices = rng.permutation(n)

        self._train = self._features.iloc[indices[:n_train]].copy()
        self._test = self._features.iloc[indices[n_train:]].copy()
        self._train["split"] = "train"
        self._test["split"] = "test"

        logger.info(
            "Split: train=%d test=%d (seed=%d)",
            len(self._train), len(self._test), self.random_state,
        )

    # ───────────────────────────────────────────────────────────
    # 4. Stats (TRAIN ONLY)
    # ───────────────────────────────────────────────────────────

    def compute_train_statistics(self) -> dict[str, float]:
        """Compute imputation stats from TRAIN only (Unit 9, pp. 76-77)."""
        if self._train is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        def _median(series: pd.Series) -> float:
            if series.dropna().empty:
                return 0.0
            return float(series.median())

        self._train_stats = {
            "gpa_median": _median(self._train["gpa"]),
            "attendance_median": _median(self._train["attendance"]),
            "avg_score_median": _median(self._train["avg_score"]),
        }
        logger.info("Train statistics: %s", self._train_stats)
        return self._train_stats

    # ───────────────────────────────────────────────────────────
    # 5. Apply Stats (to TRAIN + TEST)
    # ───────────────────────────────────────────────────────────

    def apply_statistics(self) -> None:
        """Apply TRAIN statistics to both TRAIN and TEST."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")
        if not self._train_stats:
            raise FeatureEngineeringError(
                "Call compute_train_statistics() first."
            )

        for name, col in (
            ("gpa_median", "gpa"),
            ("attendance_median", "attendance"),
            ("avg_score_median", "avg_score"),
        ):
            fill = self._train_stats[name]
            n_train = int(self._train[col].isna().sum())
            n_test = int(self._test[col].isna().sum())
            self._train[col] = self._train[col].fillna(fill)
            self._test[col] = self._test[col].fillna(fill)
            if n_train or n_test:
                logger.info(
                    "Imputed %s: train=%d test=%d value=%.4f",
                    col, n_train, n_test, fill,
                )

        # Recompute derived features after imputation
        for df in (self._train, self._test):
            df["attendance_rate"] = (df["attendance"] / 100.0).round(4)
            df["academic_risk_score"] = (
                (4.0 - df["gpa"])
                + ((100.0 - df["attendance"]) / 25.0)
            ).round(4)
            df["performance_level"] = df["avg_score"].apply(
                self._classify_performance
            )

    # ───────────────────────────────────────────────────────────
    # 6. City Features (TRAIN ONLY — after split)
    # ───────────────────────────────────────────────────────────

    def compute_city_rank(self) -> None:
        """Compute city_rank and city_score_gap using TRAIN-only stats.

        Called AFTER split_train_test() to prevent leakage (Unit 9,
        pp. 76-77). Adds two columns:
          - city_score_gap: numeric, leak-safe
          - city_rank:      integer rank using TRAIN peers only
        """
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        # ─── If no 'city' column, mark as unavailable ───────────
        if "city" not in self._train.columns:
            logger.warning(
                "No 'city' column — city_rank/city_score_gap set to NA."
            )
            for df in (self._train, self._test):
                df["city_rank"] = pd.array([pd.NA] * len(df), dtype="Int64")
                df["city_score_gap"] = np.nan
            return

        # ─── TRAIN-only reference stats ─────────────────────────
        train_city_median: dict[str, float] = (
            self._train.dropna(subset=["city"])
            .groupby("city")["avg_score"]
            .median()
            .to_dict()
        )
        train_city_scores: dict[str, list[float]] = (
            self._train.dropna(subset=["city", "avg_score"])
            .groupby("city")["avg_score"]
            .apply(lambda s: sorted(s.values, reverse=True))
            .to_dict()
        )
        fallback_median = float(
            self._train["avg_score"].dropna().median()
            if not self._train["avg_score"].dropna().empty
            else 0.0
        )

        # ─── Helpers ────────────────────────────────────────────
        def _gap(city: Any, avg: float) -> float:
            if pd.isna(city) or pd.isna(avg):
                return 0.0
            ref = train_city_median.get(city, fallback_median)
            return round(float(avg - ref), 4)

        def _rank(city: Any, avg: float) -> Any:
            if pd.isna(city) or pd.isna(avg):
                return pd.NA
            scores = train_city_scores.get(city)
            if not scores:
                return pd.NA
            # 1 + count(train peers with strictly higher score)
            rank = 1 + sum(1 for s in scores if s > avg)
            return rank

        # ─── Apply to both sets ─────────────────────────────────
        for df in (self._train, self._test):
            df["city_score_gap"] = [
                _gap(c, a)
                for c, a in zip(df["city"], df["avg_score"])
            ]
            df["city_rank"] = pd.array(
                [_rank(c, a)
                 for c, a in zip(df["city"], df["avg_score"])],
                dtype="Int64",
            )

        logger.info(
            "City features computed from TRAIN-only stats: %d cities, "
            "fallback_median=%.4f",
            len(train_city_median),
            fallback_median,
        )

    # ───────────────────────────────────────────────────────────
    # 7. Validate
    # ───────────────────────────────────────────────────────────

    def validate(self) -> None:
        """Run quality checks; raise on failure."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError("Call split_train_test() first.")

        full = pd.concat([self._train, self._test], ignore_index=True)

        # ─── Grain ──────────────────────────────────────────────
        if not full["student_id"].is_unique:
            raise FeatureEngineeringError(
                "student_id must be unique (grain = 1 student)."
            )

        # ─── No NaN in critical features ────────────────────────
        critical = [
            "attendance_rate", "academic_risk_score",
            "performance_level", "avg_score", "gpa",
        ]
        for col in critical:
            if full[col].isna().any():
                raise FeatureEngineeringError(
                    f"Column '{col}' contains NaN after imputation."
                )

        # ─── Ranges ─────────────────────────────────────────────
        if not full["attendance_rate"].between(0.0, 1.0).all():
            raise FeatureEngineeringError("attendance_rate out of [0, 1].")
        if not full["gpa"].between(0.0, 4.0).all():
            raise FeatureEngineeringError("gpa out of [0, 4].")

        # ─── Categories ─────────────────────────────────────────
        allowed = {label for _, label in PERFORMANCE_BINS}
        unknown = set(full["performance_level"].unique()) - allowed
        if unknown:
            raise FeatureEngineeringError(
                f"Unknown performance_level values: {unknown}"
            )

        # ─── Split column ───────────────────────────────────────
        if set(full["split"].unique()) != {"train", "test"}:
            raise FeatureEngineeringError(
                "split column must contain only {train, test}."
            )

        logger.info("Validation passed for %d students.", len(full))

    # ───────────────────────────────────────────────────────────
    # 8. Save
    # ───────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist features, metadata, and split."""
        if self._train is None or self._test is None:
            raise FeatureEngineeringError(
                "Nothing to save — call split_train_test() first."
            )

        full = pd.concat([self._train, self._test], ignore_index=True)
        full = full.sort_values("student_id").reset_index(drop=True)

        features_path = self.gold_dir / "ml_features.parquet"
        split_path = self.gold_dir / "train_test_split.parquet"
        metadata_path = self.gold_dir / "feature_metadata.json"

        full.drop(columns=["split"]).to_parquet(
            features_path, index=False
        )
        full[["student_id", "split"]].to_parquet(
            split_path, index=False
        )

        metadata = {
            "version": "v4.0.0-dev",
            "phase": "A",
            "grain": "1 student",
            "n_rows": int(len(full)),
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

    def run(self) -> pd.DataFrame:
        """Run the full pipeline end-to-end."""
        logger.info("=" * 60)
        logger.info("Feature Engineering — Phase A (v4.0.0-dev)")
        logger.info("=" * 60)

        self.load_gold()
        self.build_base_features()
        self.split_train_test()
        self.compute_train_statistics()
        self.apply_statistics()
        self.compute_city_rank()   # ← AFTER split (leak-safe)
        self.validate()
        self.save()

        logger.info("=" * 60)
        logger.info("DONE. ml_features.parquet written.")
        logger.info("=" * 60)

        return (
            pd.concat([self._train, self._test], ignore_index=True)
            .sort_values("student_id")
            .reset_index(drop=True)
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
        df: pd.DataFrame, cols: set[str], table: str
    ) -> None:
        missing = cols - set(df.columns)
        if missing:
            raise SchemaMismatchError(
                f"Table '{table}' missing columns: {sorted(missing)}. "
                f"Available: {sorted(df.columns)}"
            )

    @staticmethod
    def _classify_performance(avg: float) -> str:
        if pd.isna(avg):
            return "Weak"
        for threshold, label in PERFORMANCE_BINS:
            if avg >= threshold:
                return label
        return "Weak"

    @staticmethod
    def _resolve_attendance(
        students: pd.DataFrame, perf: pd.DataFrame
    ) -> pd.Series:
        """Resolve attendance from multiple sources with fallbacks.

        Priority:
          1. dim_students.attendance
          2. fact_student_performance.attendance
          3. data/processed/csv/csv_clean.csv (CSV pipeline output)
          4. Constant 100.0 (documented fallback)
        """
        # Source 1
        if "attendance" in students.columns:
            series = pd.to_numeric(
                students["attendance"], errors="coerce"
            )
            if series.notna().any():
                logger.info("Attendance: from dim_students.attendance.")
                return series

        # Source 2
        if "attendance" in perf.columns:
            agg = perf.groupby("student_id")["attendance"].mean()
            series = students["student_id"].map(agg).astype(float)
            if series.notna().any():
                logger.info(
                    "Attendance: from fact_student_performance.attendance."
                )
                return series

        # Source 3 — CSV pipeline
        if CSV_FALLBACK.exists():
            try:
                csv_df = pd.read_csv(CSV_FALLBACK)
                if {"student_id", "attendance"}.issubset(csv_df.columns):
                    csv_df["attendance"] = pd.to_numeric(
                        csv_df["attendance"], errors="coerce"
                    )
                    csv_map = csv_df.set_index("student_id")["attendance"]
                    series = (
                        students["student_id"].map(csv_map).astype(float)
                    )
                    if series.notna().any():
                        logger.info(
                            "Attendance: from %s (CSV pipeline).",
                            CSV_FALLBACK.name,
                        )
                        return series
                else:
                    logger.warning(
                        "CSV lacks required columns: %s",
                        list(csv_df.columns),
                    )
            except Exception as exc:
                logger.warning("Failed to read %s: %s", CSV_FALLBACK, exc)

        # Fallback
        logger.warning(
            "No attendance source found; defaulting to 100.0. "
            "attendance_rate will be constant 1.0."
        )
        return pd.Series(100.0, index=students.index, dtype=float)

    @staticmethod
    def _compute_score_change(perf: pd.DataFrame) -> pd.DataFrame:
        """Compute mean of consecutive score deltas per student."""
        df = perf.copy()

        order_col = None
        for cand in ("assessment_id", "id"):
            if cand in df.columns:
                order_col = cand
                break
        if order_col is None:
            df = df.reset_index().rename(columns={"index": "_row_id"})
            order_col = "_row_id"

        group_cols = ["student_id"]
        if "course_id" in df.columns:
            group_cols.append("course_id")

        df = df.sort_values(group_cols + [order_col])
        df["_prev"] = df.groupby(group_cols)["score"].shift(1)
        df["_delta"] = df["score"] - df["_prev"]

        return (
            df.dropna(subset=["_delta"])
            .groupby("student_id", as_index=False)
            .agg(score_change=("_delta", "mean"))
        )


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    engineer = FeatureEngineer()
    df = engineer.run()
    print()
    print("=" * 60)
    print("Preview: ml_features.parquet")
    print("=" * 60)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()