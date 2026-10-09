"""Database Layer — SQLite connection + safe SQL script execution."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def connect(db_file: Path) -> sqlite3.Connection:
    """
    Open a SQLite connection with foreign keys enforced.

    SQLite disables foreign key enforcement by default (per-connection
    setting). We enable it explicitly so that referential integrity is
    honored at the storage layer (Unit 4, pp. 14-15).

    Caller is responsible for closing — prefer `with connect(...)`.
    """
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")

    # Defensive: verify enforcement actually took effect.
    # Some SQLite builds silently ignore PRAGMA in edge cases.
    fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    logger.info(
        "Connected to %s (foreign_keys=%s)",
        db_file,
        "ENABLED" if fk_status else "DISABLED",
    )
    return conn


def execute_sql_file(conn: sqlite3.Connection, sql_file: Path) -> None:
    """
    Execute a .sql file containing multiple statements.

    Uses `executescript` which is atomic per call.
    """
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    sql_text = sql_file.read_text(encoding="utf-8")
    logger.info("Executing SQL file: %s", sql_file)
    conn.executescript(sql_text)
    conn.commit()
    logger.info("SQL file executed successfully: %s", sql_file)


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check whether a table exists in the database."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cur.fetchone() is not None


def count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    """Return the number of rows in a table. Raises if table missing."""
    if not table_exists(conn, table_name):
        raise ValueError(f"Table does not exist: {table_name}")
    cur = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cur.fetchone()[0])
