Student Data Engineering Pipeline

End-to-End Data Engineering Pipeline — from raw CSV, JSON, and relational/document databases to validated, ML-ready datasets, with SQL, PostgreSQL, SQLite, MongoDB, quality reporting, and full test coverage.









Current version: 3.0.0 — see CHANGELOG.md for details.

Overview

This project demonstrates production-grade Data Engineering across eight integrated units:

Unit 1 — Data Engineering Fundamentals: CSV-based ETL pipeline (Python + Pandas)

Unit 2 — Relational Databases & SQL: PostgreSQL + SQLite extraction layer

Unit 3 — Advanced SQL: Subqueries, CTEs, Window Functions, Ranking

Unit 4 — Database Design: Normalization (1NF, 2NF, 3NF)

Unit 5 — Python for Data Engineering: Multi-source ETL patterns

Unit 6 — Pandas / Polars: Data processing and performance

Unit 7 — APIs & Web Scraping: Data acquisition

Unit 8 — MongoDB & NoSQL: Document databases + 5 independent pipelines

All pathways converge on the same goal: producing validated, ML-ready datasets.

What's Inside

Unit 1 — CSV Pipeline (8 layers)


svgsvg

CSV → LOAD → VALIDATE SCHEMA → CONVERT TYPES → CLEAN
→ VALIDATE FINAL → SAVE (CSV + SQLite) → QUALITY REPORT

text


Unit 2 — Database Layer (5 tables, dual engine)


svgsvg

PostgreSQL (primary) → SQL Queries → DataFrame → Validation → CSV
SQLite (fallback) → SQL Queries → DataFrame → Validation → CSV

text


Unit 3 — Advanced SQL


svgsvg

Analytics Layer: Subqueries + CTEs + CASE + Window Functions + Ranking + LAG/LEAD

text


Unit 8 — Multi-Source Pipeline Architecture (NEW in v3.0.0)


svgsvg

5 independent source pipelines (BasePipeline abstract class):

+----------+ +----------+ +----------+ +----------+ +----------+
| CSV | | SQLite | |PostgreSQL| | MongoDB | | JSON |
+----+-----+ +----+-----+ +----+-----+ +----+-----+ +----+-----+
| | | | |
+-------------+-------------+-------------+-------------+
|
v
Extract → Transform → Validate → Load
|
v
data/processed/{source}/{source}_clean.csv
|
v
Comparison Report

text


Each pipeline inherits from BasePipeline and implements:

extract() — read from source

transform() — clean + standardize (6 columns)

validate() — check correctness

load() — save output

Run all:

python pipelines/run_all_pipelines.py
python pipelines/compare_pipelines.py

svgsvg

Result: 5 CSV outputs + 1 comparison report in ~0.6 seconds.

Architecture

Unit 1 Pipeline

text

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
                    [8] REPORT          report_layer.generate_quality_report
                            |
                            v
                     ML-READY DATASET

svgsvg

Unit 2 Database Layer (PostgreSQL + SQLite)

text

   Relational Database (PostgreSQL / SQLite)
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

svgsvg

Unit 8 Multi-Source Layer

text

CSV  ---+
JSON ---+
SQLite -+-→ BasePipeline (abstract)
Postgres+    +- extract()
MongoDB-+    +- transform()   → 6 standard columns
             +- validate()
             +- load()        → data/processed/{src}/{src}_clean.csv
                    |
                    v
         compare_pipelines.py → comparison_report.md

svgsvg

Quick Start

Install Python dependencies

bash

pip install -r requirements.txt

svgsvg

Unit 1 Pipeline (CSV)

bash

python main.py

svgsvg

Unit 2 Database (SQLite — Python)

bash

# 1. Build the SQLite database
python scripts/build_university_db.py

# 2. Export ML features to CSV
python scripts/export_student_report.py

svgsvg

Unit 2 Database (PostgreSQL — pgAdmin)

See docs/POSTGRESQL_SETUP.md for step-by-step setup.

sql

-- Once PostgreSQL is running, open pgAdmin → Query Tool
-- Run files in this order:
-- 1. database/queries/postgresql/01_schema.sql
-- 2. database/queries/postgresql/02_seed_data.sql
-- 3. database/queries/postgresql/03_verify.sql

svgsvg

Unit 8 Multi-Source Pipelines

bash

# Run all 5 pipelines
python pipelines/run_all_pipelines.py

# Generate comparison report
python pipelines/compare_pipelines.py

# Check environment (Python + services + files)
python scripts/check_environment.py

svgsvg

MongoDB (Unit 8)

bash

# Build MongoDB collection (idempotent)
python scripts/build_mongodb.py

# Explore with demos
python scripts/mongodb_read.py
python scripts/mongodb_update.py
python scripts/mongodb_pipeline.py

svgsvg

Test Everything

bash

pytest tests/ -v

svgsvg

Docker

bash

docker build -t student-pipeline .
docker run --rm -v $(pwd)/data:/app/data student-pipeline

svgsvg

CLI Options (Unit 1 Pipeline)

Flag

Short

Default

Description

--raw

-r

data/raw/students_raw.csv

Input CSV path

--output

-o

data/processed/students_ml_ready.csv

Output CSV path

--db

-d

data/student_data.db

SQLite path

--verbose

-v

off

Enable DEBUG logging

--no-verify

—

off

Skip post-save verification

--version

—

—

Show version

Exit Codes

Code

Meaning

0

Success

1

Unexpected error

2

File not found

3

Validation error

130

Interrupted (Ctrl+C)

Database Layer (Unit 2)

Tables

Table

Purpose

Rows

instructors

Teaching staff

4

students

Enrolled students

8

courses

Offered courses

5

enrollments

Student ↔ Course (M)

13

assessments

Grades

26

Tri-Engine Support

Engine

Use Case

Where

SQLite

Embedded, testing, Python integration

data/raw/university.db

PostgreSQL

Production, advanced SQL, multi-user

pgAdmin

MongoDB

Semi-structured, nested documents

University_Ai.students (Compass)

SQL Query Catalog

Folder

Purpose

database/queries/*.sql

Basic SQL (SELECT, WHERE, JOINs)

database/queries/postgresql/

PostgreSQL-specific (schema, seed, verify, CASE, subqueries, CTEs, window functions)

database/queries/advanced/

SQLite advanced queries

database/mongodb/

MongoDB query catalog + README

Full details: database/queries/postgresql/README.md

PostgreSQL Setup

Complete setup guide (installation → schema → data → first query):

docs/POSTGRESQL_SETUP.md

MongoDB Setup

MongoDB integration guide (Unit 8):

docs/MONGODB.md

ML Feature Extraction

The canonical ML-ready table:

sql

SELECT
    s.student_id,
    s.full_name       AS student_name,
    s.city,
    COUNT(DISTINCT e.course_id) AS courses_count,
    COUNT(a.assessment_id)      AS assessments_count,
    ROUND(AVG(a.score)::numeric, 2) AS average_score,
    MAX(a.score)                AS highest_score,
    MIN(a.score)                AS lowest_score
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
LEFT JOIN assessments a ON s.student_id = a.student_id
GROUP BY s.student_id, s.full_name, s.city
ORDER BY average_score DESC;

svgsvg

Multi-Source Pipelines (Unit 8)

Pipeline Comparison

Source

Rows

Columns

Missing

Notes

CSV

8

6

0

Complete

SQLite

8

6

16

No attendance column

PostgreSQL

8

6

16

No attendance column

MongoDB

10

6

0

Semi-structured + 2 extra

JSON

3

6

0

Demo dataset

Total

37

—

32

~0.6s runtime

Standardized Schema (6 columns)

All pipelines output the same schema:

Column

Type

Range

student_id

Int64

> 0

name

string

—

age

Int64

16-80

gpa

float64

0.0-4.0

attendance

float64

0-100

city

string

—

Interpretation of Missing Values

The 16 missing values in SQLite/PostgreSQL are not a bug — they accurately reflect the source schemas (no attendance column). This demonstrates why multi-source pipelines need a standardization layer.

Full details: docs/PIPELINE_ARCHITECTURE.md

Project Layout

text

student_data_pipeline/
+-- data/
|   +-- raw/
|   |   +-- students_raw.csv          # Unit 1 input
|   |   +-- students_raw.json         # Unit 8 input
|   |   +-- university.db             # Unit 2 SQLite database
|   +-- processed/
|   |   +-- csv/csv_clean.csv
|   |   +-- sqlite/sqlite_clean.csv
|   |   +-- postgres/postgres_clean.csv
|   |   +-- mongodb/mongodb_clean.csv
|   |   +-- json/json_clean.csv
|   +-- comparison/
|   |   +-- comparison_report.md
|   |   +-- comparison_data.csv
|   +-- student_data.db
+-- database/
|   +-- schema.sql
|   +-- seed_data.sql
|   +-- queries/
|   |   +-- basic.sql
|   |   +-- aggregates.sql
|   |   +-- joins.sql
|   |   +-- reports.sql
|   |   +-- advanced/
|   |   +-- postgresql/
|   +-- mongodb/
|       +-- README.md
|       +-- queries.md
+-- docs/
|   +-- DATABASE.md
|   +-- POSTGRESQL_SETUP.md
|   +-- MONGODB.md
|   +-- PIPELINE_ARCHITECTURE.md
+-- logs/
|   +-- pipeline.log
+-- pipelines/
|   +-- __init__.py
|   +-- base_pipeline.py
|   +-- csv_pipeline.py
|   +-- sqlite_pipeline.py
|   +-- postgres_pipeline.py
|   +-- mongodb_pipeline.py
|   +-- json_pipeline.py
|   +-- run_all_pipelines.py
|   +-- compare_pipelines.py
|   +-- README.md
+-- scripts/
|   +-- build_university_db.py
|   +-- export_student_report.py
|   +-- run_sql_file.py
|   +-- build_mongodb.py
|   +-- mongodb_read.py
|   +-- mongodb_update.py
|   +-- mongodb_pipeline.py
|   +-- check_environment.py
+-- src/
|   +-- config.py
|   +-- logging_setup.py
|   +-- io_layer.py
|   +-- transform_layer.py
|   +-- validate_layer.py
|   +-- storage_layer.py
|   +-- report_layer.py
|   +-- orchestrator.py
|   +-- db_layer.py
|   +-- query_layer.py
|   +-- mongo_layer.py
+-- tests/
+-- legacy/
|   +-- main_v1.py
+-- main.py
+-- requirements.txt
+-- pytest.ini
+-- Dockerfile
+-- .gitignore
+-- ARCHITECTURE.md
+-- CHANGELOG.md
+-- README.md

svgsvg

Data Quality Rules

Rule

Constraint

student_id

Unique, non-null, integer

name

Non-null

age

Between 16 and 80

gpa

Between 0 and 4

attendance

Between 0 and 100

city

Filled with "Unknown" if missing

Missing-Value Policy

Column

Policy

name

Drop row

city

Fill with "Unknown"

age

Fill with median

gpa

Fill with median

attendance

Fill with median

Database Constraints

Table

Constraint

instructors

email UNIQUE

students

gender IN ('Male', 'Female')

courses

credit_hours > 0

enrollments

UNIQUE(student, course, semester)

assessments

score BETWEEN 0 AND 100

assessments

assessment_type IN (Midterm, Final, Quiz, Project)

Testing

bash

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov=pipelines --cov-report=html

svgsvg

Test breakdown:

Layer

File

Tests

I/O

test_io.py

8

Transform

test_transform.py

13

Validate

test_validate.py

10

Storage

test_storage.py

6

Orchestrator

test_orchestrator.py

5

Database

test_db_layer.py

10

Query

test_query_layer.py

9

Total



61

Technologies

Python 3.10+

pandas 2.2+ — data manipulation

PostgreSQL 18 — production-grade RDBMS

SQLite 3 — embedded relational database

MongoDB 7.0 — document-oriented database (NoSQL)

SQL — SELECT, WHERE, JOIN, GROUP BY, HAVING, Aggregates, Subqueries, CTEs, Window Functions

pytest 8+ — testing framework

Docker — containerization

GitHub Actions — CI/CD

Design Principles

Architecture First — layout decided before code

Single Responsibility — one responsibility per layer

Immutability — every transformer copies before mutating

Fail Fast — validate at the earliest boundary

Error Accumulation — collect all errors, then raise

Exception Chaining — preserve root cause with raise ... from

Idempotency — safe to re-run

Type Hints — every function signature

Defensive Programming — each layer is safe by default

Open/Closed — BasePipeline is closed for modification, open for extension

Template Method — run() defines skeleton, subclasses fill stages

Full details: ARCHITECTURE.md

Documentation

File

Purpose

README.md

How to use the project (this file)

ARCHITECTURE.md

Why the project is designed this way

CHANGELOG.md

Version history (SemVer)

docs/DATABASE.md

ERD, constraints, query catalog

docs/POSTGRESQL_SETUP.md

PostgreSQL setup guide

docs/MONGODB.md

MongoDB integration guide

docs/PIPELINE_ARCHITECTURE.md

Multi-source pipeline architecture

database/queries/postgresql/README.md

PostgreSQL query docs

License

MIT © 2026