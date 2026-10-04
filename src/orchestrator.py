"""Orchestrator Layer — Coordinates the pipeline stages."""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import pandas as pd

from src.config import (
    DB_FILE,
    OUTPUT_FILE,
    RAW_FILE,
    SEPARATOR,
)
from src.io_layer import load_data, save_data
from src.report_layer import generate_quality_report
from src.storage_layer import save_to_sqlite
from src.transform_layer import clean_data, convert_data_types
from src.validate_layer import validate_data, validate_schema

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    success: bool
    total_rows: int
    input_file: str
    output_file: str
    db_file: str
    duration_seconds: float
    quality_report: pd.DataFrame = field(repr=False, compare=False)


@contextmanager
def timed(label: str) -> Iterator[None]:
    """Measure and log the duration of a block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("[%s] took %.4fs", label, elapsed)


def run_pipeline(
    raw_file: Path = RAW_FILE,
    output_file: Path = OUTPUT_FILE,
    db_file: Path = DB_FILE,
    verify_save: bool = True,
) -> PipelineResult:
    """Run the complete 9-stage pipeline."""
    start = time.perf_counter()
    logger.info(SEPARATOR)
    logger.info("Pipeline started.")
    logger.info(SEPARATOR)

    # 1. Extract
    with timed("LOAD"):
        df = load_data(raw_file)

    # 2. Validate schema
    with timed("VALIDATE_SCHEMA"):
        validate_schema(df)

    # 3. Transform types
    with timed("CONVERT_TYPES"):
        df = convert_data_types(df)

    # 4. Clean
    with timed("CLEAN"):
        df = clean_data(df)

    # 5. Final validation
    with timed("VALIDATE_FINAL"):
        validate_data(df)

    # 6. Save CSV
    with timed("SAVE_CSV"):
        save_data(df, output_file, verify=verify_save)

    # 7. Save SQLite
    with timed("SAVE_SQLITE"):
        save_to_sqlite(df, db_file)

    # 8. Quality report
    with timed("REPORT"):
        report = generate_quality_report(df)

    # 9. Display
    logger.info(SEPARATOR)
    logger.info("DATA QUALITY REPORT (%d rows)", len(df))
    logger.info("\n%s", report.to_string(index=False))
    logger.info(SEPARATOR)
    logger.info("ML-READY DATASET (first 20 rows)")
    logger.info("\n%s", df.head(20).to_string(index=False))
    logger.info(SEPARATOR)

    duration = time.perf_counter() - start
    logger.info("Pipeline completed successfully in %.2fs.", duration)
    logger.info(SEPARATOR)

    return PipelineResult(
        success=True,
        total_rows=len(df),
        input_file=str(raw_file),
        output_file=str(output_file),
        db_file=str(db_file),
        duration_seconds=duration,
        quality_report=report,
    )
