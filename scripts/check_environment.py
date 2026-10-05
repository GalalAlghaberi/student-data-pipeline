"""
Environment check — verify all dependencies and services.
Run: python scripts/check_environment.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
from datetime import datetime


def check(title: str, fn) -> bool:
    """Run a check function, return True/False."""
    try:
        result = fn()
        status = "OK" if result else "FAIL"
        symbol = "[+]" if result else "[-]"
        print(f"{symbol} {title:40} {status}")
        return result
    except Exception as exc:
        print(f"[-] {title:40} EXCEPTION: {exc}")
        return False


def main():
    print("=" * 70)
    print(f"ENVIRONMENT CHECK — {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    print("PYTHON & PACKAGES")
    print("-" * 70)

    # Python version
    check(
        "Python >= 3.10",
        lambda: sys.version_info >= (3, 10),
    )

    # Packages
    check("pandas", lambda: __import__("pandas") and True)
    check("numpy", lambda: __import__("numpy") and True)
    check("pymongo", lambda: __import__("pymongo") and True)
    check("psycopg2", lambda: __import__("psycopg2") and True)
    check("pytest", lambda: __import__("pytest") and True)

    print()
    print("SERVICES")
    print("-" * 70)

    # MongoDB
    def check_mongo():
        from pymongo import MongoClient
        c = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        c.admin.command("ping")
        count = c["University_Ai"]["students"].count_documents({})
        c.close()
        print(f"    -> MongoDB: {count} documents in University_Ai.students")
        return count > 0

    check("MongoDB (localhost:27017)", check_mongo)

    # PostgreSQL
    def check_postgres():
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            dbname=os.getenv("PG_DB", "university_training"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "postgres"),
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        count = cur.fetchone()[0]
        conn.close()
        print(f"    -> PostgreSQL: {count} rows in students")
        return count > 0

    check("PostgreSQL (localhost:5432)", check_postgres)

    print()
    print("DATA FILES")
    print("-" * 70)

    files = {
        "CSV": "data/raw/students_raw.csv",
        "SQLite": "data/raw/university.db",
        "JSON": "data/raw/students_raw.json",
    }
    for name, path in files.items():
        p = Path(path)
        check(f"{name} ({path})", lambda p=p: p.exists())

    print()
    print("PIPELINE MODULES")
    print("-" * 70)

    modules = [
        "pipelines.base_pipeline",
        "pipelines.csv_pipeline",
        "pipelines.sqlite_pipeline",
        "pipelines.postgres_pipeline",
        "pipelines.mongodb_pipeline",
        "pipelines.json_pipeline",
    ]
    for mod in modules:
        check(mod, lambda m=mod: __import__(m) and True)

    print()
    print("=" * 70)
    print("ENVIRONMENT CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()