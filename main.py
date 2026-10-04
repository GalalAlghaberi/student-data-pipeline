"""
Student Performance Data Pipeline — Production Grade
=====================================================

End-to-end Data Engineering pipeline:
    Raw CSV → Validated + Cleaned + ML-Ready Dataset
             + SQLite + Quality Report.

Course: Data Engineering and Databases for AI — Unit 1
Version: 2.0.0
License: MIT
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.config import (
    DB_FILE,
    EXIT_FILE_NOT_FOUND,
    EXIT_INTERRUPTED,
    EXIT_SUCCESS,
    EXIT_UNEXPECTED,
    EXIT_VALIDATION_ERROR,
    OUTPUT_FILE,
    RAW_FILE,
)
from src.logging_setup import setup_logging
from src.orchestrator import run_pipeline

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="student-pipeline",
        description="Student Data Engineering Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py\n"
            "  python main.py --raw data/other.csv\n"
            "  python main.py --output /tmp/out.csv --verbose\n"
            "  python main.py --no-verify\n"
        ),
    )
    parser.add_argument(
        "--raw", "-r", type=Path, default=RAW_FILE,
        help=f"Input CSV (default: {RAW_FILE})",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=OUTPUT_FILE,
        help=f"Output CSV (default: {OUTPUT_FILE})",
    )
    parser.add_argument(
        "--db", "-d", type=Path, default=DB_FILE,
        help=f"SQLite file (default: {DB_FILE})",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    parser.add_argument(
        "--no-verify", action="store_true",
        help="Skip post-save verification (faster).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        result = run_pipeline(
            raw_file=args.raw,
            output_file=args.output,
            db_file=args.db,
            verify_save=not args.no_verify,
        )
        logger.info(
            "Execution summary: %d rows in %.2fs → %s",
            result.total_rows,
            result.duration_seconds,
            result.output_file,
        )
        return EXIT_SUCCESS

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user (Ctrl+C).")
        print("\n⚠  Operation cancelled.", file=sys.stderr)
        return EXIT_INTERRUPTED

    except FileNotFoundError as exc:
        logger.error("Input file not found: %s", exc)
        print(f"\n❌ Input file not found: {exc}", file=sys.stderr)
        return EXIT_FILE_NOT_FOUND

    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n❌ Validation error:\n{exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR

    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        print(f"\n❌ Pipeline failed: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(main())
