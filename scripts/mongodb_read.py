"""
MongoDB Read Operations Demo — Unit 8
Run: python scripts/mongodb_read.py
"""
import sys
from pathlib import Path

# Add project root to Python path (so `from src.mongo_layer import ...` works)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from src.mongo_layer import (
    get_collection,
    read_all, read_by_city, read_by_gpa_range,
    read_by_skills, read_with_projection,
    read_high_performers, read_by_project_year,
    count_by_city, avg_gpa_by_city, top_skills,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def section(title: str):
    logger.info("=" * 60)
    logger.info(f"  {title}")
    logger.info("=" * 60)


def main():
    client, collection = get_collection()
    try:
        section("1. Read ALL students")
        students = read_all(collection)
        logger.info(f"Total: {len(students)} students")

        section("2. Filter: city = Sanaa")
        for s in read_by_city(collection, "Sanaa"):
            logger.info(f"  - {s['personal']['name']} (GPA: {s['academic']['gpa']})")

        section("3. Filter: 3.5 <= GPA <= 4.0")
        for s in read_by_gpa_range(collection, 3.5, 4.0):
            logger.info(f"  - {s['personal']['name']}: {s['academic']['gpa']}")

        section("4. Filter: has BOTH Python and SQL")
        for s in read_by_skills(collection, ["Python", "SQL"], require_all=True):
            logger.info(f"  - {s['personal']['name']}: {s['skills']}")

        section("5. Filter: has Python OR Polars")
        logger.info(f"Found: {len(read_by_skills(collection, ['Python', 'Polars'], require_all=False))} students")

        section("6. Projection: only name + GPA")
        for p in read_with_projection(collection, {"_id": 0, "personal.name": 1, "academic.gpa": 1}):
            logger.info(f"  - {p}")

        section("7. High performers: GPA >= 3.5 AND attendance >= 90")
        for p in read_high_performers(collection, 3.5, 90):
            logger.info(f"  - {p['personal']['name']}: GPA={p['academic']['gpa']}, Att={p['academic']['attendance']}")

        section("8. Students with completed project in 2026")
        for p in read_by_project_year(collection, 2026, "Completed"):
            logger.info(f"  - {p['personal']['name']}")

        section("9. Aggregation: student count by city")
        for row in count_by_city(collection):
            logger.info(f"  - {row['city']}: {row['count']}")

        section("10. Aggregation: average GPA by city")
        for row in avg_gpa_by_city(collection):
            logger.info(f"  - {row['city']}: avg={row['average_gpa']:.2f} ({row['student_count']} students)")

        section("11. Aggregation: top 5 skills")
        for row in top_skills(collection, limit=5):
            logger.info(f"  - {row['skill']}: {row['count']} students")

    finally:
        client.close()


if __name__ == "__main__":
    main()