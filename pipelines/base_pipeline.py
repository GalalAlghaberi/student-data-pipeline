"""
Base Pipeline — Template for all source-specific pipelines.
Unit 5 + Unit 8: Pipeline Architecture.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime, timezone
import logging
import time
import pandas as pd

logger = logging.getLogger(__name__)


class PipelineResult:
    """Standardized result from any pipeline."""

    def __init__(self, source, rows_in, rows_out, columns, duration, output_path, errors=None):
        self.source = source
        self.rows_in = rows_in
        self.rows_out = rows_out
        self.columns = columns
        self.duration = duration
        self.output_path = output_path
        self.errors = errors or []
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "source": self.source,
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "column_count": len(self.columns),
            "columns": ",".join(self.columns),
            "duration_seconds": round(self.duration, 4),
            "output_path": str(self.output_path),
            "errors": "; ".join(self.errors) if self.errors else "",
            "timestamp": self.timestamp,
        }


class BasePipeline(ABC):
    """Base class for all source pipelines."""

    SOURCE_NAME: str = "base"
    STANDARD_COLUMNS = ["student_id", "name", "age", "gpa", "attendance", "city"]

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"pipeline.{self.SOURCE_NAME}")

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        raise NotImplementedError

    def load(self, df: pd.DataFrame) -> Path:
        output_path = self.output_dir / f"{self.SOURCE_NAME}_clean.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")
        return output_path

    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all STANDARD_COLUMNS exist (fill missing with None)."""
        for col in self.STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[self.STANDARD_COLUMNS]

    def run(self) -> PipelineResult:
        start = time.perf_counter()
        self.logger.info("=" * 60)
        self.logger.info(f"PIPELINE: {self.SOURCE_NAME.upper()}")
        self.logger.info("=" * 60)

        raw_df = pd.DataFrame()
        errors = []

        try:
            self.logger.info("[1/4] Extract...")
            raw_df = self.extract()
            self.logger.info(f"      -> {len(raw_df)} rows x {len(raw_df.columns)} cols")

            self.logger.info("[2/4] Transform...")
            clean_df = self.transform(raw_df.copy())
            self.logger.info(f"      -> {len(clean_df)} rows x {len(clean_df.columns)} cols")

            self.logger.info("[3/4] Validate...")
            self.validate(clean_df)
            self.logger.info("      -> PASSED")

            self.logger.info("[4/4] Load...")
            output_path = self.load(clean_df)
            self.logger.info(f"      -> Saved: {output_path}")

            duration = time.perf_counter() - start
            self.logger.info(f"DONE in {duration:.3f}s")

            return PipelineResult(
                source=self.SOURCE_NAME,
                rows_in=len(raw_df),
                rows_out=len(clean_df),
                columns=list(clean_df.columns),
                duration=duration,
                output_path=output_path,
            )

        except Exception as exc:
            duration = time.perf_counter() - start
            self.logger.error(f"FAILED after {duration:.3f}s: {exc}")
            errors.append(f"{type(exc).__name__}: {exc}")
            return PipelineResult(
                source=self.SOURCE_NAME,
                rows_in=len(raw_df),
                rows_out=0,
                columns=[],
                duration=duration,
                output_path=Path(""),
                errors=errors,
            )