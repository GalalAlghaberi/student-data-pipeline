# PostgreSQL Queries — University Training Database

> PostgreSQL implementation of the University Training Database.
> Companion to the SQLite version used in the Python pipeline.

---

## Overview

This folder contains **PostgreSQL-specific SQL files** that implement the University Training Database and demonstrate advanced SQL techniques covered in **Units 2 and 3**:

- Full relational schema with constraints
- Basic and advanced queries (SELECT, WHERE, JOIN, GROUP BY)
- Subqueries, CTEs, and CASE expressions
- Window Functions (ranking, LAG/LEAD, running totals)
- Comprehensive analytical reports

Uses PostgreSQL's richer feature set:
- `::numeric` casting for precise ROUND
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
| 3 | `03_verify.sql` | Verify row counts | ✅ Any time |
| 4 | `04_case_queries.sql` | CASE + RANK example | ✅ Any time |
| 5 | `05_subqueries.sql` | Subqueries | ✅ Any time |
| 6 | `06_ctes.sql` | Common Table Expressions | ✅ Any time |
| 7 | `07_window_functions.sql` | Window Functions | ✅ Any time |
| 8 | `08_ranking.sql` | ROW_NUMBER, RANK, DENSE_RANK | ✅ Any time |
| 9 | `09_lag_lead.sql` | LAG, LEAD, Running Totals | ✅ Any time |
| 10 | `10_student_analytics.sql` | Final Project (8 reports) | ✅ Any time |

---

## Files in Detail

### `01_schema.sql` — Schema

Creates 5 tables with full constraints:

| Table | Rows |
|-------|------|
| `instructors` | 4 |
| `students` | 8 |
| `courses` | 5 |
| `enrollments` | 13 |
| `assessments` | 26 |

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

---

### `02_seed_data.sql` — Sample Data

Inserts **51 rows** across 5 tables in the correct foreign-key order.

---

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

---

### `04_case_queries.sql` — CASE + Ranking

First advanced query: **Student Ranking** using CTE + `RANK() OVER`.

**Output:** 8 rows (one per student), sorted by average score descending.

---

### `05_subqueries.sql` — Subqueries

**6 queries** demonstrating:

- `IN (SELECT ...)`
- `NOT IN (SELECT ...)`
- `EXISTS (SELECT ...)`
- Subquery in `WHERE`
- Subquery in `SELECT`
- Comparing to average

---

### `06_ctes.sql` — Common Table Expressions

**7 queries** demonstrating:

- Single CTE
- CTE + WHERE
- CTE + JOIN
- Multiple CTEs
- CTE + CASE
- CTE + Window Function
- CTE + Aggregate

---

### `07_window_functions.sql` — Window Functions

**10 queries** demonstrating:

- `AVG() OVER (PARTITION BY ...)` — student/course/university averages
- `SUM() OVER (...)` — student total
- `MAX() / MIN() / COUNT() OVER (...)` — group statistics
- `CASE + Window Function` — classifying positions

**Key insight:** `GROUP BY` collapses rows; `OVER` preserves them and adds the computed value.

---

### `08_ranking.sql` — Ranking Functions

**10 queries** demonstrating:

- `ROW_NUMBER()` — unique sequential numbers
- `RANK()` — ties with gaps
- `DENSE_RANK()` — ties without gaps
- Top-N per group (best 1, best 2 per student)
- Top 3 students university-wide
- Honor roll with 🥇🥈🥉 medals

**Difference summary:**

| Score | `ROW_NUMBER` | `RANK` | `DENSE_RANK` |
|-------|-------------|--------|--------------|
| 100 | 1 | 1 | 1 |
| 100 | 2 | 1 | 1 |
| 95 | 3 | 3 | 2 |
| 90 | 4 | 4 | 3 |

---

### `09_lag_lead.sql` — LAG, LEAD, Running Totals

**11 queries** demonstrating:

- `LAG()` — previous row value
- `LEAD()` — next row value
- `score - LAG(score)` — progress analysis
- `CASE + LAG` — classify improvement/decline
- `SUM() OVER (...)` — running total per student
- `AVG() OVER (...)` — running average
- Window frame: `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`

**Use case:** Track student performance change across Midterm → Final assessments.

---

### `10_student_analytics.sql` — Final Project

**8 comprehensive reports** combining all concepts:

| # | Report | Purpose |
|---|--------|---------|
| 1 | **Top 3 Students** | Best performers |
| 2 | **Student Ranking** | University-wide RANK + DENSE_RANK |
| 3 | **City Ranking** | Rank within each city |
| 4 | **Course Ranking** | Best courses by avg score |
| 5 | **Performance Classification** | Excellent / Very Good / Good / Weak |
| 6 | **Progress Analysis** | LAG-based, per assessment |
| 7 | **Running Score** | Running total + running average |
| 8 | **Consolidated Analytics** | The final ML-ready table |

**Final output columns:**

```
student_id | student_name | city | courses_count | assessments_count |
average_score | highest_score | lowest_score |
university_rank | city_rank | diff_from_avg | performance_level
```

**Sample output:**

| student_id | student_name | city | avg | rank | level |
|---|---|---|---|---|---|
| 1008 | Noor Saleh | Sanaa | 97.00 | 1 | Excellent |
| 1006 | Huda Mohammed | Dhamar | 93.50 | 2 | Excellent |
| 1002 | Sara Mohammed | Dhamar | 92.25 | 3 | Excellent |
| 1004 | Mona Saleh | Taiz | 86.25 | 4 | Very Good |
| 1001 | Ahmed Ali | Sanaa | 83.00 | 5 | Very Good |
| 1007 | Ali Hassan | Ibb | 76.50 | 6 | Good |
| 1003 | Khaled Hassan | Ibb | 74.00 | 7 | Good |
| 1005 | Omar Ahmed | Sanaa | 68.75 | 8 | Needs Improvement |

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

### In pgAdmin (recommended)

1. **Connect** to `university_training`
2. Open **Query Tool** (`Ctrl+E`)
3. **Open file** (`Ctrl+O`) → select the `.sql` file
4. Press **`F5`** to execute

### In `psql` (command line)

```bash
psql -U postgres -d university_training -f 01_schema.sql
psql -U postgres -d university_training -f 02_seed_data.sql
psql -U postgres -d university_training -f 03_verify.sql
psql -U postgres -d university_training -f 10_student_analytics.sql
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

---

### `ERROR: duplicate key value violates unique constraint`

**Cause:** You're re-running `02_seed_data.sql`.

**Fix:** Same as above — either skip or clear tables.

---

### `ERROR: syntax error at or near "::"`

**Cause:** You're running a PostgreSQL query on SQLite.

**Fix:** Use the corresponding file in `database/queries/advanced/` for SQLite.

---

## Related Files

- **Setup guide:** [`docs/POSTGRESQL_SETUP.md`](../../../docs/POSTGRESQL_SETUP.md)
- **SQLite version:** [`database/queries/advanced/`](../advanced/)
- **ERD:** [`docs/DATABASE.md`](../../../docs/DATABASE.md)
- **Unit 2 review:** [`07_unit2_review.sql`](07_unit2_review.sql)
- **Practice tasks:** [`Practice Tasks.sql`](Practice%20Tasks.sql)
- **Mini task:** [`Mini_Task.sql`](Mini_Task.sql)

---

## Execution Checklist

Before running the queries, verify:

- [ ] PostgreSQL 18 installed and running
- [ ] Database `university_training` created
- [ ] Server registered in pgAdmin
- [ ] Connected to the correct database
- [ ] Files executed in correct order (1 → 10)

---

## Progress Summary

| Unit | Topic | Files | Status |
|------|-------|-------|--------|
| **Unit 2** | Relational DB + SQL basics | 01-06 | ✅ Complete |
| **Unit 3** | Advanced SQL | 07-10 | ✅ Complete |

**Unit 3 covers:**
- Subqueries
- CTEs (single + multiple)
- CASE expressions
- Window Functions
- Ranking (ROW_NUMBER, RANK, DENSE_RANK)
- LAG / LEAD
- Running Totals
- Analytical reporting

---

**Last updated:** 2026-10-05