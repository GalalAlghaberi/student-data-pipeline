"""
MongoDB Update & Delete Demo — Unit 8
Run: python scripts/mongodb_update.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from src.mongo_layer import (
    get_collection,
    update_gpa, add_skill, remove_skill,
    increment_attendance, upsert_student, delete_by_id,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def section(title: str):
    logger.info("=" * 60)
    logger.info(f"  {title}")
    logger.info("=" * 60)


def show(collection, student_id: int):
    s = collection.find_one({"student_id": student_id})
    if s:
        logger.info(
            f"  -> {s['personal']['name']}: "
            f"GPA={s['academic']['gpa']}, "
            f"Att={s['academic']['attendance']}, "
            f"Skills={s['skills']}"
        )


def main():
    client, collection = get_collection()
    try:
        section("1. UPDATE: GPA of 1001 (3.5 -> 3.75)")
        logger.info("Before:"); show(collection, 1001)
        logger.info(f"Modified: {update_gpa(collection, 1001, 3.75)}")
        logger.info("After:"); show(collection, 1001)

        section("2. UPDATE: add 'Docker' to 1001")
        logger.info(f"Modified: {add_skill(collection, 1001, 'Docker')}")
        show(collection, 1001)
        logger.info("Adding 'Docker' again (should not duplicate):")
        logger.info(f"Modified: {add_skill(collection, 1001, 'Docker')}")
        show(collection, 1001)

        section("3. UPDATE: remove 'Docker' from 1001")
        logger.info(f"Modified: {remove_skill(collection, 1001, 'Docker')}")
        show(collection, 1001)

        section("4. UPDATE: increment attendance of 1001 by +3")
        logger.info("Before:"); show(collection, 1001)
        logger.info(f"Modified: {increment_attendance(collection, 1001, 3)}")
        logger.info("After:"); show(collection, 1001)

        section("5. UPSERT: student 2001 (new)")
        new = {
            "student_id": 2001,
            "personal": {"name": "Fatima Al-Qadhi", "age": 20, "city": "Sanaa", "country": "Yemen"},
            "skills": ["Python", "SQL", "MongoDB"],
            "academic": {"gpa": 3.6, "attendance": 93},
            "projects": [],
        }
        logger.info(f"Result: {upsert_student(collection, new)}")
        show(collection, 2001)

        section("6. DELETE: remove student 2001")
        logger.info(f"Before: {collection.count_documents({})} students")
        logger.info(f"Deleted: {delete_by_id(collection, 2001)}")
        logger.info(f"After:  {collection.count_documents({})} students")

        section("7. VERIFICATION")
        logger.info(f"Total: {collection.count_documents({})}")
        show(collection, 1001)

    finally:
        client.close()


if __name__ == "__main__":
    main()
