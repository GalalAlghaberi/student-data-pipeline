"""Query Layer — execute SQL queries and return pandas DataFrames."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def run_query(
    conn: sqlite3.Connection,
    query: str,
) -> pd.DataFrame:
    """
    Execute a SELECT query and return the result as a DataFrame.

    Raises:
        ValueError: if the query returns no columns.
    """
    logger.info("Executing query (first 60 chars): %s", query.strip()[:60])
    try:
        df = pd.read_sql_query(query, conn)
    except pd.errors.DatabaseError as exc:
        raise RuntimeError(f"Query failed: {exc}") from exc

    if df.empty and df.columns.empty:
        raise ValueError("Query returned no columns.")

    logger.info("Query returned %d rows × %d columns", len(df), df.shape[1])
    return df


def run_query_file(
    conn: sqlite3.Connection,
    sql_file: Path,
) -> pd.DataFrame:
    """
    Run a .sql file that contains a single SELECT statement.

    Strips SQL comments before executing.
    """
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    raw = sql_file.read_text(encoding="utf-8")

    # Remove line comments (-- ...) so pandas receives a single clean query
    lines = [
        line for line in raw.splitlines()
        if not line.strip().startswith("--")
    ]
    query = "\n".join(lines).strip()

    if not query:
        raise ValueError(f"No executable SQL in {sql_file}")

    return run_query(conn, query)


def load_ml_features(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Return the canonical ML-ready feature table.

    Columns:
        student_id, student_name, city,
        courses_count, assessments_count,
        average_score, highest_score, lowest_score
    """
    query = """
    SELECT
        s.student_id,
        s.full_name       AS student_name,
        s.city,
        COUNT(DISTINCT e.course_id) AS courses_count,
        COUNT(a.assessment_id)      AS assessments_count,
        ROUND(AVG(a.score), 2)      AS average_score,
        MAX(a.score)                AS highest_score,
        MIN(a.score)                AS lowest_score
    FROM students s
    LEFT JOIN enrollments e ON s.student_id = e.student_id
    LEFT JOIN assessments a ON s.student_id = a.student_id
    GROUP BY s.student_id, s.full_name, s.city
    ORDER BY average_score DESC
    """
    return run_query(conn, query)
