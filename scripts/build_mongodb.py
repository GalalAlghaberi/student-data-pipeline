"""
Build MongoDB database with semi-structured student data.
Unit 8 - MongoDB & NoSQL
"""
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "University_Ai"           # الاسم الصحيح
COLLECTION_NAME = "students"


def get_client() -> MongoClient:
    """Create and verify MongoDB connection."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client


def build_students_data() -> list[dict]:
    """Semi-structured student documents."""
    retrieved_at = datetime.now(timezone.utc).isoformat()
    return [
        {
            "student_id": 1001,
            "personal": {"name": "Ahmed Ali", "age": 22, "city": "Sanaa", "country": "Yemen"},
            "skills": ["Python", "SQL", "MongoDB"],
            "academic": {"gpa": 3.5, "attendance": 92},
            "projects": [
                {"name": "AI Pipeline", "year": 2026, "status": "Completed",
                 "technologies": ["Python", "PostgreSQL"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1002,
            "personal": {"name": "Sara Mohammed", "age": 21, "city": "Dhamar", "country": "Yemen"},
            "skills": ["Pandas", "NumPy", "Polars", "Python"],
            "academic": {"gpa": 3.8, "attendance": 96},
            "projects": [
                {"name": "Data Dashboard", "year": 2026, "status": "Completed",
                 "technologies": ["Pandas", "Streamlit"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1003,
            "personal": {"name": "Khaled Hassan", "age": 23, "city": "Ibb", "country": "Yemen"},
            "skills": ["Java", "Spring Boot"],
            "academic": {"gpa": 3.1, "attendance": 88},
            "projects": [],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1004,
            "personal": {"name": "Mona Saleh", "age": 20, "city": "Taiz", "country": "Yemen"},
            "skills": ["Python", "SQL", "MongoDB", "Docker"],
            "academic": {"gpa": 4.0, "attendance": 98},
            "projects": [
                {"name": "ML Classifier", "year": 2026, "status": "In Progress",
                 "technologies": ["scikit-learn", "Python"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1005,
            "personal": {"name": "Ali Ahmed", "age": 25, "city": "Sanaa", "country": "Yemen"},
            "skills": ["Python", "SQL"],
            "academic": {"gpa": 3.6, "attendance": 90},
            "projects": [
                {"name": "ETL Pipeline", "year": 2025, "status": "Completed",
                 "technologies": ["Python", "PostgreSQL", "Pandas"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1006,
            "personal": {"name": "Huda Omar", "age": 22, "city": "Dhamar", "country": "Yemen"},
            "skills": ["Python", "SQL", "MongoDB", "Polars"],
            "academic": {"gpa": 3.9, "attendance": 95},
            "projects": [
                {"name": "Analytics Dashboard", "year": 2026, "status": "Completed",
                 "technologies": ["Polars", "Plotly"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1007,
            "personal": {"name": "Mohammed Noor", "age": 19, "city": "Sanaa", "country": "Yemen"},
            "skills": ["Python"],
            "academic": {"gpa": 2.9, "attendance": 81},
            "projects": [],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1008,
            "personal": {"name": "Noor Saleh", "age": 21, "city": "Sanaa", "country": "Yemen"},
            "skills": ["Python", "Pandas", "NumPy"],
            "academic": {"gpa": 3.7, "attendance": 94},
            "projects": [
                {"name": "Sales Analysis", "year": 2025, "status": "Completed",
                 "technologies": ["Pandas"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1009,
            "personal": {"name": "Yousef Kamal", "age": 24, "city": "Aden", "country": "Yemen"},
            "skills": ["Java", "Python", "MongoDB"],
            "academic": {"gpa": 3.4, "attendance": 89},
            "projects": [
                {"name": "NoSQL Migration", "year": 2026, "status": "In Progress",
                 "technologies": ["MongoDB", "Python"]}
            ],
            "retrieved_at": retrieved_at,
        },
        {
            "student_id": 1010,
            "personal": {"name": "Layla Nasser", "age": 20, "city": "Taiz", "country": "Yemen"},
            "skills": ["Python", "SQL", "Docker", "MongoDB", "Polars"],
            "academic": {"gpa": 3.95, "attendance": 97},
            "projects": [
                {"name": "Data Pipeline", "year": 2026, "status": "Completed",
                 "technologies": ["Python", "Polars", "MongoDB"]}
            ],
            "retrieved_at": retrieved_at,
        },
    ]


def create_indexes(collection):
    """Unique + query indexes."""
    collection.create_index([("student_id", ASCENDING)], unique=True)
    collection.create_index([("personal.city", ASCENDING)])
    collection.create_index([("academic.gpa", ASCENDING)])
    logger.info("Indexes created.")


def create_validation_schema(db):
    """JSON Schema validation on a separate collection."""
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["student_id", "personal", "academic"],
            "properties": {
                "student_id": {"bsonType": "int"},
                "personal": {
                    "bsonType": "object",
                    "required": ["name", "city"],
                },
                "academic": {
                    "bsonType": "object",
                    "required": ["gpa"],
                    "properties": {
                        "gpa": {"bsonType": "double", "minimum": 0, "maximum": 4},
                        "attendance": {"bsonType": "int", "minimum": 0, "maximum": 100},
                    },
                },
                "skills": {"bsonType": "array"},
            },
        }
    }
    if "validated_students" in db.list_collection_names():
        db.drop_collection("validated_students")
    db.create_collection("validated_students", validator=validator)
    logger.info("Validation schema created for 'validated_students'.")


def main():
    client = None
    try:
        client = get_client()
        logger.info("Connected to MongoDB.")

        db = client[DB_NAME]

        if COLLECTION_NAME in db.list_collection_names():
            db.drop_collection(COLLECTION_NAME)
            logger.info(f"Dropped existing '{COLLECTION_NAME}' collection.")

        collection = db[COLLECTION_NAME]
        documents = build_students_data()
        result = collection.insert_many(documents)
        logger.info(f"Inserted {len(result.inserted_ids)} documents.")

        create_indexes(collection)
        create_validation_schema(db)

        count = collection.count_documents({})
        logger.info(f"Total documents in '{COLLECTION_NAME}': {count}")
        logger.info(f"Database: {DB_NAME}")
        logger.info(f"Collections: {db.list_collection_names()}")

    except Exception as exc:
        logger.error(f"Failed: {exc}")
        raise
    finally:
        if client:
            client.close()
            logger.info("Connection closed.")


if __name__ == "__main__":
    main()