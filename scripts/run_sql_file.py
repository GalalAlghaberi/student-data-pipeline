"""
Run a .sql file against university.db, showing results for each query.

Usage:
    python scripts/run_sql_file.py database/queries/advanced/01_case.sql
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "data" / "raw" / "university.db"


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """
    Split SQL into (title, query) pairs.

    Rules:
      - A query starts after a `-- Qn: ...` comment block.
      - Anything BEFORE the first `-- Qn:` is discarded (header comments).
      - Other full-line comments are ignored.
    """
    lines = sql_text.splitlines()
    queries: list[tuple[str, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect title like: -- Q1: ...  or  -- Q1. ...
        m = re.match(r"^--\s*Q\d+[:.]?\s*(.+)$", stripped)
        if m:
            # Save previous query (only if it has a title)
            if current_title is not None and current_lines:
                queries.append((current_title, "\n".join(current_lines).strip()))
            # Start new query
            current_title = m.group(1).strip()
            current_lines = []
            continue

        # Skip comments/blank lines if we're still in the header
        if current_title is None:
            continue

        # Skip full-line comments inside a query
        if stripped.startswith("--"):
            continue

        current_lines.append(line)

    # Save the last query
    if current_title is not None and current_lines:
        queries.append((current_title, "\n".join(current_lines).strip()))

    return queries


def main(sql_file: Path) -> int:
    if not DB_FILE.exists():
        print(f"❌ Database not found: {DB_FILE}")
        return 1
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return 1

    sql_text = sql_file.read_text(encoding="utf-8")
    queries = split_queries(sql_text)

    print(f"\n{'=' * 70}")
    print(f"📄 {sql_file.name} — {len(queries)} queries")
    print(f"🗄️  {DB_FILE}")
    print(f"{'=' * 70}")

    conn = sqlite3.connect(DB_FILE)
    try:
        for i, (title, query) in enumerate(queries, start=1):
            q = query if query.endswith(";") else query + ";"
            print(f"\n{'─' * 70}")
            print(f"▶ Query {i}: {title}")
            print(f"{'─' * 70}")
            try:
                df = pd.read_sql_query(q, conn)
                if df.empty:
                    print("   (no rows)")
                else:
                    print(df.to_string(index=False))
                    print(f"\n   → {len(df)} row(s)")
            except Exception as exc:
                print(f"   ❌ Error: {exc}")
    finally:
        conn.close()

    print(f"\n{'=' * 70}")
    print("✅ Done")
    print(f"{'=' * 70}\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_sql_file.py <file.sql>")
        sys.exit(1)
    sys.exit(main(Path(sys.argv[1])))
