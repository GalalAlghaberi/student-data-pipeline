"""Run all 7 source pipelines independently.

Sources:
    1. CSV       (data/raw/students_raw.csv)
    2. SQLite    (data/raw/university.db)
    3. PostgreSQL (localhost:5432)
    4. MongoDB   (localhost:27017)
    5. JSON      (data/raw/students_raw.json)
    6. API       (dummyjson.com/users + cache fallback)
    7. Scraper   (data/raw/web_students.html)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from pipelines.csv_pipeline import CSVPipeline
from pipelines.sqlite_pipeline import SQLitePipeline
from pipelines.postgres_pipeline import PostgresPipeline
from pipelines.mongodb_pipeline import MongoDBPipeline
from pipelines.json_pipeline import JSONPipeline
from pipelines.api_pipeline import APIPipeline
from pipelines.scraper_pipeline import ScraperPipeline

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

    # 6. API (uses cache fallback if network fails)
    try:
        p = APIPipeline(output_dir=ROOT / "data/processed/api")
        results.append(p.run())
    except Exception as exc:
        logger.error(f"API failed: {exc}")

    # 7. Scraper (local HTML fixture)
    try:
        p = ScraperPipeline(output_dir=ROOT / "data/processed/scraper")
        results.append(p.run())
    except Exception as exc:
        logger.error(f"Scraper failed: {exc}")

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    for r in results:
        status = "OK" if not r.errors else "FAIL"
        logger.info(f"[{status}] {r.source}: {r.rows_out} rows in {r.duration:.3f}s")


if __name__ == "__main__":
    main()