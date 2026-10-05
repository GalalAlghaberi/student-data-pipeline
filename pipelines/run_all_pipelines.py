"""Run all 4 source pipelines independently."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from pipelines.csv_pipeline import CSVPipeline
from pipelines.sqlite_pipeline import SQLitePipeline
from pipelines.postgres_pipeline import PostgresPipeline
from pipelines.mongodb_pipeline import MongoDBPipeline
from pipelines.json_pipeline import JSONPipeline
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("run_all")

ROOT = Path(__file__).resolve().parent.parent


def main():
    results = []

    # 1. CSV
    try:
        p = CSVPipeline(
            output_dir=ROOT / "data/processed/csv",
            input_file=ROOT / "data/raw/students_raw.csv",
        )
        results.append(p.run())
    except Exception as exc:
        logger.error(f"CSV failed: {exc}")

    # 2. SQLite
    try:
        p = SQLitePipeline(
            output_dir=ROOT / "data/processed/sqlite",
            db_file=ROOT / "data/raw/university.db",
        )
        results.append(p.run())
    except Exception as exc:
        logger.error(f"SQLite failed: {exc}")

    # 3. PostgreSQL
    try:
        p = PostgresPipeline(output_dir=ROOT / "data/processed/postgres")
        results.append(p.run())
    except Exception as exc:
        logger.error(f"PostgreSQL failed: {exc}")

    # 4. MongoDB
    try:
        p = MongoDBPipeline(output_dir=ROOT / "data/processed/mongodb")
        results.append(p.run())
    except Exception as exc:
        logger.error(f"MongoDB failed: {exc}")
    # 5. JSON
    try:
        p = JSONPipeline(
            output_dir=ROOT / "data/processed/json",
            input_file=ROOT / "data/raw/students_raw.json",
        )
        results.append(p.run())
    except Exception as exc:
        logger.error(f"JSON failed: {exc}")

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for r in results:
        status = "OK" if not r.errors else "FAIL"
        logger.info(f"[{status}] {r.source}: {r.rows_out} rows in {r.duration:.3f}s")


if __name__ == "__main__":
    main()