"""
MongoDB -> Pandas Pipeline — Unit 8
Semi-structured data -> ML-ready DataFrame.
Run: python scripts/mongodb_pipeline.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from datetime import datetime, timezone
from src.mongo_layer import (
    get_collection, read_all, avg_gpa_by_city, top_skills,
    to_dataframe, add_features,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/processed")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client, collection = get_collection()
    try:
        logger.info("STAGE 1: Extracting from MongoDB...")
        records = read_all(collection)
        logger.info(f"  -> Extracted {len(records)} documents")

        logger.info("STAGE 2: Converting to DataFrame...")
        df = to_dataframe(records)
        logger.info(f"  -> Shape: {df.shape}")
        logger.info(f"  -> Columns: {list(df.columns)}")

        logger.info("STAGE 3: Engineering features...")
        df = add_features(df)
        new_cols = [c for c in df.columns if c.startswith("skill_") or c in ("attendance_rate", "project_count")]
        logger.info(f"  -> Added: {new_cols}")

        logger.info("STAGE 4: Validating...")
        assert df["student_id"].is_unique, "student_id must be unique"
        assert df["academic.gpa"].between(0, 4).all(), "GPA must be 0-4"
        assert df["academic.attendance"].between(0, 100).all(), "Attendance must be 0-100"
        logger.info("  -> Validation passed")

        logger.info("STAGE 5: Saving ML-ready CSV...")
        output = OUTPUT_DIR / "students_mongodb.csv"
        df.to_csv(output, index=False)
        logger.info(f"  -> Saved: {output}")

        logger.info("STAGE 6: Aggregations...")
        logger.info("  -> Avg GPA by city:")
        for row in avg_gpa_by_city(collection):
            logger.info(f"      {row['city']}: {row['average_gpa']:.2f} ({row['student_count']})")
        logger.info("  -> Top 5 skills:")
        for row in top_skills(collection, limit=5):
            logger.info(f"      {row['skill']}: {row['count']}")

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED")
        logger.info(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info(f"  Documents: {len(records)}")
        logger.info(f"  Features:  {len(df.columns)}")
        logger.info(f"  Output:    {output}")
        logger.info("=" * 60)
    finally:
        client.close()


if __name__ == "__main__":
    main()
