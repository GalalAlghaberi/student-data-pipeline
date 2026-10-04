# University Training Database

> A relational database for practicing SQL and Data Engineering concepts,
> integrated with the main Python pipeline.

---

## Overview

The database models a **university training system** with 5 related tables:

| Table | Purpose | Rows |
|---|---|---|
| `instructors` | Teaching staff | 4 |
| `students` | Enrolled students | 8 |
| `courses` | Offered courses | 5 |
| `enrollments` | Student ↔ Course (M:N bridge) | 13 |
| `assessments` | Grades (Midterm/Final/Quiz/Project) | 26 |

---

## Entity-Relationship Diagram

```
  ┌──────────────┐
  │ instructors  │
  │--------------│
  │ instructor_id│◄────┐
  │ full_name    │     │
  │ department   │     │ 1:N
  │ email        │     │
  └──────────────┘     │
                       │
  ┌──────────────┐  ┌──┴───────────┐
  │ students     │  │ courses      │
  │--------------│  │--------------│
  │ student_id   │  │ course_id    │
  │ full_name    │  │ course_name  │
  │ gender       │  │ credit_hours │
  │ date_of_birth│  │ instructor_id│
  │ city         │  └──┬───────────┘
  └──────┬───────┘     │
         │             │
         │ 1:N   1:N   │
         ▼             ▼
  ┌──────────────────────┐
  │ enrollments          │
  │----------------------│
  │ enrollment_id (PK)   │
  │ student_id   (FK)    │
  │ course_id    (FK)    │
  │ enrollment_date      │
  │ semester             │
  │ UNIQUE(student,      │
  │        course,       │
  │        semester)     │
  └──────────────────────┘

         │ 1:N   1:N   │
         ▼             ▼
  ┌──────────────────────┐
  │ assessments          │
  │----------------------│
  │ assessment_id (PK)   │
  │ student_id    (FK)   │
  │ course_id     (FK)   │
  │ assessment_type      │
  │ score (0-100)        │
  └──────────────────────┘
```

---

## Constraints Enforced

| Table | Constraint | Purpose |
|---|---|---|
| `instructors` | `email UNIQUE` | No duplicate emails |
| `students` | `gender CHECK` | Only 'Male' / 'Female' |
| `courses` | `credit_hours CHECK > 0` | No zero-credit courses |
| `enrollments` | `UNIQUE(student, course, semester)` | Prevent re-enrollment |
| `assessments` | `score CHECK 0-100` | Valid grade range |
| `assessments` | `assessment_type CHECK` | Only valid types |

**Foreign Keys:**
- `courses.instructor_id → instructors.instructor_id`
- `enrollments.student_id → students.student_id`
- `enrollments.course_id → courses.course_id`
- `assessments.student_id → students.student_id`
- `assessments.course_id → courses.course_id`

---

## Query Catalog

| File | Purpose |
|---|---|
| `database/queries/basic.sql` | SELECT, WHERE, ORDER BY |
| `database/queries/aggregates.sql` | COUNT, AVG, MIN, MAX, GROUP BY, HAVING |
| `database/queries/joins.sql` | INNER JOIN, LEFT JOIN, Multi-Table |
| `database/queries/reports.sql` | Analytical reports + ML feature table |

---

## Build & Export Workflow

```bash
# 1. Build the database from scratch
python scripts/build_university_db.py

# 2. Export the ML feature table to CSV
python scripts/export_student_report.py
```

**Output:**
- `data/raw/university.db` — SQLite database
- `data/processed/student_performance.csv` — ML-ready features

---

## ML Feature Table

The canonical ML-ready table is built via:

```sql
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
ORDER BY average_score DESC;
```

**Why LEFT JOIN?** — keeps students with no enrollments/assessments (defensive).

---

## Connection to Unit 1

This database integrates with the main pipeline:

```
Unit 1 Pipeline:  CSV → Cleaning → Validation → ML-ready CSV
                                   ▲
                                   │
Unit 2 adds:      SQLite DB ──► SQL Extraction ──► Pandas ──► CSV
```

**Both pathways converge on ML-ready CSV.**

---

## Testing

| File | Focus | Tests |
|---|---|---|
| `tests/test_db_layer.py` | Connection + SQL execution | 10 |
| `tests/test_query_layer.py` | SQL → DataFrame | 9 |

Run all:

```bash
pytest tests/ -v
```

**Total tests: 61**