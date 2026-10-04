# Student Data Engineering Pipeline

> **End-to-End Data Engineering Pipeline** — from raw CSV and relational databases to validated, ML-ready datasets, with SQL, SQLite, quality reporting, and full test coverage.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/pandas-2.2%2B-green)](https://pandas.pydata.org/)
[![SQLite](https://img.shields.io/badge/sqlite-3-blue)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/tests-61%20passed-brightgreen)](#testing)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](CHANGELOG.md)

**Current version: [2.0.0](CHANGELOG.md)** — see [CHANGELOG.md](CHANGELOG.md) for details.

---

## Overview

This project demonstrates **production-grade Data Engineering** across two integrated units:

- **Unit 1 — Data Engineering Fundamentals**: CSV-based ETL pipeline
- **Unit 2 — Relational Databases & SQL**: SQLite + SQL extraction layer

Both pathways converge on the same goal: **producing validated, ML-ready datasets**.

---

## What's Inside

### Unit 1 — CSV Pipeline (8 layers)

```
CSV → LOAD → VALIDATE SCHEMA → CONVERT TYPES → CLEAN
    → VALIDATE FINAL → SAVE (CSV + SQLite) → QUALITY REPORT
```

### Unit 2 — Database Layer (5 tables)

```
university.db  →  SQL Queries  →  DataFrame  →  Validation  →  CSV
```

---

## Architecture

### Unit 1 Pipeline

```
                RAW CSV
                    |
                    v
            [1] LOAD             io_layer.load_data
                    |
                    v
            [2] VALIDATE SCHEMA  validate_layer.validate_schema
                    |
                    v
            [3] CONVERT TYPES    transform_layer.convert_data_types
                    |
                    v
            [4] CLEAN            transform_layer.clean_data
                    |
                    v
            [5] VALIDATE FINAL   validate_layer.validate_data
                    |
            +-------+-------+
            v               v
        [6] SAVE        [7] SAVE
            CSV             SQLite
            +-------+-------+
                    v
            [8] REPORT           report_layer.generate_quality_report
                    |
                    v
             ML-READY DATASET
```

### Unit 2 Database Layer

```
   Relational Database (university.db)
                    |
                    v
            SQL Extraction (query_layer)
                    |
                    v
          DataFrame (pandas)
                    |
                    v
          Validation (score ranges, columns)
                    |
                    v
       student_performance.csv (ML features)
```

---

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Run Unit 1 Pipeline (CSV)

```bash
python main.py
```

### Run Unit 2 (Database)

```bash
# 1. Build the database from scratch
python scripts/build_university_db.py

# 2. Export ML features to CSV
python scripts/export_student_report.py
```

### Test Everything

```bash
pytest tests/ -v
```

### Docker

```bash
docker build -t student-pipeline .
docker run --rm -v $(pwd)/data:/app/data student-pipeline
```

---

## CLI Options (Unit 1 Pipeline)

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--raw` | `-r` | `data/raw/students_raw.csv` | Input CSV path |
| `--output` | `-o` | `data/processed/students_ml_ready.csv` | Output CSV path |
| `--db` | `-d` | `data/student_data.db` | SQLite path |
| `--verbose` | `-v` | off | Enable DEBUG logging |
| `--no-verify` | — | off | Skip post-save verification |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected error |
| 2 | File not found |
| 3 | Validation error |
| 130 | Interrupted (Ctrl+C) |

---

## Database Layer (Unit 2)

### Tables

| Table | Purpose | Rows |
|-------|---------|------|
| `instructors` | Teaching staff | 4 |
| `students` | Enrolled students | 8 |
| `courses` | Offered courses | 5 |
| `enrollments` | Student ↔ Course (M:N) | 13 |
| `assessments` | Grades | 26 |

### Schema Highlights

- **Primary Keys**: every table has an integer PK
- **Foreign Keys**: enforced with `PRAGMA foreign_keys = ON`
- **Constraints**: `UNIQUE`, `CHECK`, `NOT NULL`
- **Indexes**: on all FK columns for fast joins

Full ERD: [`docs/DATABASE.md`](docs/DATABASE.md)

### SQL Query Catalog

| File | Focus |
|------|-------|
| `database/queries/basic.sql` | SELECT, WHERE, ORDER BY |
| `database/queries/aggregates.sql` | COUNT, AVG, MIN, MAX, GROUP BY, HAVING |
| `database/queries/joins.sql` | INNER JOIN, LEFT JOIN, Multi-Table |
| `database/queries/reports.sql` | Analytical reports + ML features |

### ML Feature Extraction

The canonical ML-ready table:

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

**Sample Output:**

| student_id | student_name | city | courses_count | assessments_count | average_score | highest_score | lowest_score |
|---|---|---|---|---|---|---|---|
| 1008 | Noor Saleh | Sanaa | 1 | 2 | 97.00 | 98.0 | 96.0 |
| 1006 | Huda Mohammed | Dhamar | 1 | 2 | 93.50 | 95.0 | 92.0 |
| 1002 | Sara Mohammed | Dhamar | 2 | 8 | 92.25 | 95.0 | 88.0 |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

## Project Layout

```
student_data_pipeline/
├── data/
│   ├── raw/
│   │   ├── students_raw.csv          # Unit 1 input
│   │   └── university.db             # Unit 2 SQLite database
│   ├── processed/
│   │   ├── students_ml_ready.csv     # Unit 1 output
│   │   └── student_performance.csv   # Unit 2 output
│   └── student_data.db
├── database/                          # Unit 2 — SQL assets
│   ├── schema.sql                     # DDL (5 tables)
│   ├── seed_data.sql                  # 51 rows of sample data
│   └── queries/
│       ├── basic.sql
│       ├── aggregates.sql
│       ├── joins.sql
│       └── reports.sql
├── docs/
│   └── DATABASE.md                    # ERD + query catalog
├── logs/
│   └── pipeline.log                   # rotating log
├── scripts/                           # Unit 2 — executable scripts
│   ├── build_university_db.py
│   └── export_student_report.py
├── src/                               # 10 modules
│   ├── config.py
│   ├── logging_setup.py
│   ├── io_layer.py                    # CSV read/write
│   ├── transform_layer.py             # type conv + clean
│   ├── validate_layer.py              # schema + data validation
│   ├── storage_layer.py               # SQLite persistence
│   ├── report_layer.py                # quality report
│   ├── orchestrator.py                # Unit 1 coordinator
│   ├── db_layer.py                    # Unit 2 — SQLite connect
│   └── query_layer.py                 # Unit 2 — SQL → DataFrame
├── tests/                             # 61 tests
│   ├── conftest.py
│   ├── test_io.py
│   ├── test_transform.py
│   ├── test_validate.py
│   ├── test_storage.py
│   ├── test_orchestrator.py
│   ├── test_db_layer.py               # Unit 2
│   └── test_query_layer.py            # Unit 2
├── legacy/
│   └── main_v1.py                     # Original educational version
├── main.py                            # CLI entry point
├── requirements.txt
├── pytest.ini
├── Dockerfile
├── .gitignore
├── ARCHITECTURE.md                    # Design decisions
└── README.md
```

---

## Data Quality Rules (Unit 1)

| Rule | Constraint |
|------|------------|
| `student_id` | Unique, non-null, integer |
| `name` | Non-null |
| `age` | Between 16 and 80 |
| `gpa` | Between 0 and 4 |
| `attendance` | Between 0 and 100 |
| `city` | Filled with `"Unknown"` if missing |

### Missing-Value Policy

| Column | Policy |
|--------|--------|
| `name` | Drop row |
| `city` | Fill with `"Unknown"` |
| `age` | Fill with median |
| `gpa` | Fill with median |
| `attendance` | Fill with median |

---

## Database Constraints (Unit 2)

| Table | Constraint |
|-------|------------|
| `instructors` | `email UNIQUE` |
| `students` | `gender IN ('Male', 'Female')` |
| `courses` | `credit_hours > 0` |
| `enrollments` | `UNIQUE(student, course, semester)` |
| `assessments` | `score BETWEEN 0 AND 100` |
| `assessments` | `assessment_type IN (Midterm, Final, Quiz, Project)` |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

**Test breakdown:**

| Layer | File | Tests |
|-------|------|-------|
| I/O | `test_io.py` | 8 |
| Transform | `test_transform.py` | 13 |
| Validate | `test_validate.py` | 10 |
| Storage | `test_storage.py` | 6 |
| Orchestrator | `test_orchestrator.py` | 5 |
| Database | `test_db_layer.py` | 10 |
| Query | `test_query_layer.py` | 9 |
| **Total** | | **61** |

---

## Technologies

- **Python 3.10+**
- **pandas 2.2+** — data manipulation
- **SQLite 3** — embedded relational database
- **SQL** — SELECT, WHERE, JOIN, GROUP BY, HAVING, Aggregates
- **pytest 8+** — testing framework
- **Docker** — containerization
- **GitHub Actions** — CI/CD

---

## Design Principles

- **Architecture First** — layout decided before code
- **Single Responsibility** — one responsibility per layer
- **Immutability** — every transformer copies before mutating
- **Fail Fast** — validate at the earliest boundary
- **Error Accumulation** — collect all errors, then raise
- **Exception Chaining** — preserve root cause with `raise ... from`
- **Idempotency** — safe to re-run (uses `if_exists="replace"`, `exist_ok=True`)
- **Type Hints** — every function signature
- **Defensive Programming** — each layer is safe by default

Full details: [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | How to use the project (this file) |
| `ARCHITECTURE.md` | Why the project is designed this way |
| `docs/DATABASE.md` | ERD, constraints, query catalog (Unit 2) |

---

## License

MIT © 2025