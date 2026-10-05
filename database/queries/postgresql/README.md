# PostgreSQL Queries — University Training Database

> PostgreSQL implementation of the University Training Database.
> Companion to the SQLite version used in the Python pipeline.

---

## Overview

This folder contains **PostgreSQL-specific SQL files** that mirror the SQLite implementation but use PostgreSQL's richer feature set:

- `::numeric` casting for ROUND
- `EXPLAIN ANALYZE` for query plans
- Advanced window functions
- Full ACID transactions

---

## File Execution Order

> **Important:** Execute files in this exact order.

| # | File | Purpose | Re-runnable? |
|---|------|---------|--------------|
| 1 | `01_schema.sql` | Create 5 tables + indexes | ❌ Once |
| 2 | `02_seed_data.sql` | Insert sample data (51 rows) | ❌ Once |
| 3 | `03_verify.sql` | Verify counts | ✅ Any time |
| 4 | `04_case_queries.sql` | CASE + RANK example | ✅ Any time |
| 5 | `05_subqueries.sql` | Subqueries | ✅ Any time |
| 6 | `06_ctes.sql` | Common Table Expressions | ✅ Any time |

---

## Files in Detail

### `01_schema.sql` — Schema

Creates 5 tables with full constraints:

- `instructors` — 4 rows
- `students` — 8 rows
- `courses` — 5 rows
- `enrollments` — 13 rows
- `assessments` — 26 rows

**Constraints enforced:**
- Primary keys (all tables)
- Foreign keys (`ON DELETE CASCADE` / `SET NULL`)
- `CHECK` (gender, credit_hours, score, assessment_type)
- `UNIQUE` (email, student+course+semester)

**Indexes created:**
- `idx_enrollments_student`
- `idx_enrollments_course`
- `idx_assessments_student`
- `idx_assessments_course`

### `02_seed_data.sql` — Sample Data

Inserts 51 rows across 5 tables in the correct FK order.

### `03_verify.sql` — Verification

A single query that returns row counts for all 5 tables using `UNION ALL`:

```sql
SELECT 'instructors' AS table_name, COUNT(*) FROM instructors
UNION ALL SELECT 'students',    COUNT(*) FROM students
UNION ALL SELECT 'courses',     COUNT(*) FROM courses
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments
UNION ALL SELECT 'assessments', COUNT(*) FROM assessments;
```

**Expected output:**

| table_name | count |
|------------|-------|
| instructors | 4 |
| students | 8 |
| courses | 5 |
| enrollments | 13 |
| assessments | 26 |

### `04_case_queries.sql` — CASE + Ranking

First advanced query: **Student Ranking** using CTE + `RANK() OVER`.

**Output:** 8 rows (one per student), sorted by average score descending.

### `05_subqueries.sql` — Subqueries

6 queries demonstrating:
- `IN (SELECT ...)`
- `NOT IN (SELECT ...)`
- `EXISTS (SELECT ...)`
- Subquery in `WHERE`
- Subquery in `SELECT`
- Comparing to average

### `06_ctes.sql` — CTEs

7 queries demonstrating:
- Single CTE
- CTE + WHERE
- CTE + JOIN
- Multiple CTEs
- CTE + CASE
- CTE + Window Function
- CTE + Aggregate

---

## PostgreSQL vs SQLite Differences

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| `ROUND` | `ROUND(AVG(x), 2)` | `ROUND(AVG(x)::numeric, 2)` |
| Type casting | `CAST(x AS REAL)` | `x::numeric` |
| `EXPLAIN ANALYZE` | Limited | Full support |
| Window Functions | Supported (3.25+) | Full support |
| Partial indexes | Limited | Full support |
| `ILIKE` | No | Yes |

---

## How to Run

### In pgAdmin

1. **Connect** to `university_training`
2. Open **Query Tool** (`Ctrl+E`)
3. **Open file** (`Ctrl+O`) → select the `.sql` file
4. Press **`F5`** to execute

### In `psql` (command line)

```bash
psql -U postgres -d university_training -f 01_schema.sql
psql -U postgres -d university_training -f 02_seed_data.sql
psql -U postgres -d university_training -f 03_verify.sql
```

---

## Database Connection Info

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `university_training` |
| User | `postgres` |
| Password | (your password) |

---

## Common Errors

### `ERROR: relation "instructors" already exists`

**Cause:** You're re-running `01_schema.sql`.

**Fix:** Either:
- Skip `01_schema.sql` (already executed)
- Or drop tables first:
```sql
DROP TABLE IF EXISTS assessments, enrollments, courses, students, instructors CASCADE;
```

### `ERROR: duplicate key value violates unique constraint`

**Cause:** You're re-running `02_seed_data.sql`.

**Fix:** Same as above — either skip or clear tables.

### `ERROR: syntax error at or near "::"`

**Cause:** You're running a PostgreSQL query on SQLite.

**Fix:** Use the corresponding file in `database/queries/advanced/` for SQLite.

---

## Related Files

- **Setup guide:** [`docs/POSTGRESQL_SETUP.md`](../../../docs/POSTGRESQL_SETUP.md)
- **SQLite version:** [`database/queries/advanced/`](../advanced/)
- **ERD:** [`docs/DATABASE.md`](../../../docs/DATABASE.md)

---

## Execution Checklist

Before running the queries, verify:

- [ ] PostgreSQL 18 installed and running
- [ ] Database `university_training` created
- [ ] Server registered in pgAdmin
- [ ] Connected to the correct database
- [ ] Files executed in correct order (1 → 6)

---

**Last updated:** 2026-10-05