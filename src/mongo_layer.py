"""
MongoDB Layer — Unit 8
Reusable operations: read / update / delete / aggregate.
"""
from contextlib import contextmanager
from typing import Any
from pymongo import MongoClient
from pymongo.collection import Collection
import pandas as pd

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "University_Ai"
COLLECTION_NAME = "students"


def get_collection(
    uri: str = MONGO_URI,
    db_name: str = DB_NAME,
    collection_name: str = COLLECTION_NAME,
) -> tuple[MongoClient, Collection]:
    """Return (client, collection). Caller must close client."""
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client, client[db_name][collection_name]


# ==================== READ ====================

def read_all(collection: Collection) -> list[dict]:
    return list(collection.find({}))


def read_by_city(collection: Collection, city: str) -> list[dict]:
    return list(collection.find({"personal.city": city}))


def read_by_gpa_range(
    collection: Collection, min_gpa: float, max_gpa: float = 4.0
) -> list[dict]:
    return list(collection.find({
        "academic.gpa": {"$gte": min_gpa, "$lte": max_gpa}
    }))


def read_by_skills(
    collection: Collection, skills: list[str], require_all: bool = True
) -> list[dict]:
    op = "$all" if require_all else "$in"
    return list(collection.find({"skills": {op: skills}}))


def read_with_projection(collection: Collection, fields: dict) -> list[dict]:
    return list(collection.find({}, fields))


def read_high_performers(
    collection: Collection, min_gpa: float = 3.5, min_attendance: int = 90
) -> list[dict]:
    return list(collection.find({
        "$and": [
            {"academic.gpa": {"$gte": min_gpa}},
            {"academic.attendance": {"$gte": min_attendance}},
        ]
    }))


def read_by_project_year(
    collection: Collection, year: int, status: str = "Completed"
) -> list[dict]:
    return list(collection.find({
        "projects": {"$elemMatch": {"year": year, "status": status}}
    }))


def count_by_city(collection: Collection) -> list[dict]:
    pipeline = [
        {"$group": {"_id": "$personal.city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"_id": 0, "city": "$_id", "count": 1}},
    ]
    return list(collection.aggregate(pipeline))


def avg_gpa_by_city(collection: Collection) -> list[dict]:
    pipeline = [
        {"$group": {
            "_id": "$personal.city",
            "average_gpa": {"$avg": "$academic.gpa"},
            "student_count": {"$sum": 1},
        }},
        {"$sort": {"average_gpa": -1}},
        {"$project": {"_id": 0, "city": "$_id", "average_gpa": 1, "student_count": 1}},
    ]
    return list(collection.aggregate(pipeline))


def top_skills(collection: Collection, limit: int = 5) -> list[dict]:
    pipeline = [
        {"$unwind": "$skills"},
        {"$group": {"_id": "$skills", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "skill": "$_id", "count": 1}},
    ]
    return list(collection.aggregate(pipeline))


# ==================== UPDATE ====================

def update_gpa(collection: Collection, student_id: int, new_gpa: float) -> int:
    return collection.update_one(
        {"student_id": student_id},
        {"$set": {"academic.gpa": new_gpa}},
    ).modified_count


def add_skill(collection: Collection, student_id: int, skill: str) -> int:
    return collection.update_one(
        {"student_id": student_id},
        {"$addToSet": {"skills": skill}},
    ).modified_count


def remove_skill(collection: Collection, student_id: int, skill: str) -> int:
    return collection.update_one(
        {"student_id": student_id},
        {"$pull": {"skills": skill}},
    ).modified_count


def increment_attendance(collection: Collection, student_id: int, delta: int) -> int:
    return collection.update_one(
        {"student_id": student_id},
        {"$inc": {"academic.attendance": delta}},
    ).modified_count


def upsert_student(collection: Collection, document: dict) -> dict:
    result = collection.update_one(
        {"student_id": document["student_id"]},
        {"$set": document},
        upsert=True,
    )
    return {
        "matched": result.matched_count,
        "modified": result.modified_count,
        "upserted_id": str(result.upserted_id) if result.upserted_id else None,
    }


# ==================== DELETE ====================

def delete_by_id(collection: Collection, student_id: int) -> int:
    return collection.delete_one({"student_id": student_id}).deleted_count


def delete_by_city(collection: Collection, city: str) -> int:
    return collection.delete_many({"personal.city": city}).deleted_count


# ==================== PANDAS BRIDGE ====================

def to_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    for r in records:
        r.pop("_id", None)
    return pd.json_normalize(records)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "academic.attendance" in df.columns:
        df["attendance_rate"] = df["academic.attendance"] / 100
    if "skills" in df.columns:
        for skill in ["Python", "SQL", "MongoDB", "Pandas", "Polars"]:
            df[f"skill_{skill.lower()}"] = df["skills"].apply(
                lambda s: skill in s if isinstance(s, list) else False
            )
    if "projects" in df.columns:
        df["project_count"] = df["projects"].apply(
            lambda p: len(p) if isinstance(p, list) else 0
        )
    return df