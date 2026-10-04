"""Storage Layer — SQLite persistence with indexes."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _assert_safe_identifier(name: str) -> None:
    """Reject unsafe SQL identifiers (prevents injection)."""
    if not _VALID_IDENTIFIER.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}")


def save_to_sqlite(
    df: pd.DataFrame,
    db_file: Path,
    table_name: str = "students",
    create_indexes: bool = True,
) -> None:
    """
    Save DataFrame to SQLite with optional indexes.

    Uses `with` for automatic resource cleanup.
    Validates identifiers to prevent SQL injection.
    """
    _assert_safe_identifier(table_name)

    db_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(db_file) as conn:
            df.to_sql(
                table_name,
                conn,
                if_exists="replace",
                index=False,
            )

            if create_indexes:
                indexed_cols = [
                    c for c in ("student_id", "city")
                    if c in df.columns
                ]
                for col in indexed_cols:
                    index_name = f"idx_{table_name}_{col}"
                    _assert_safe_identifier(index_name)
                    conn.execute(
                        f"CREATE INDEX IF NOT EXISTS "
                        f"{index_name} ON {table_name}({col})"
                    )

    except sqlite3.Error as exc:
        raise RuntimeError(
            f"SQLite error while saving to {db_file}: {exc}"
        ) from exc

    logger.info(
        "Saved %d rows → SQLite table '%s' (%s).",
        len(df), table_name, db_file,
    )
