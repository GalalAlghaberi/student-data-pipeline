# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 2025-10-04

### Added — Unit 2: Relational Databases & SQL

- **Database schema** (`database/schema.sql`): 5 tables with full constraints
  - `instructors`, `students`, `courses`, `enrollments`, `assessments`
  - Primary keys, foreign keys (with `ON DELETE CASCADE` / `SET NULL`)
  - `CHECK`, `UNIQUE`, `NOT NULL` constraints
  - Indexes on all foreign key columns

- **Seed data** (`database/seed_data.sql`): 51 rows of realistic sample data

- **SQL query catalog** (`database/queries/`):
  - `basic.sql` — SELECT, WHERE, ORDER BY
  - `aggregates.sql` — COUNT, AVG, MIN, MAX, SUM, GROUP BY, HAVING
  - `joins.sql` — INNER JOIN, LEFT JOIN, multi-table joins
  - `reports.sql` — analytical reports + ML feature extraction

- **Database layer** (`src/db_layer.py`):
  - `connect()` — SQLite connection with `PRAGMA foreign_keys = ON`
  - `execute_sql_file()` — safe multi-statement SQL execution
  - `table_exists()`, `count_rows()` — introspection helpers

- **Query layer** (`src/query_layer.py`):
  - `run_query()` — SQL → pandas DataFrame
  - `run_query_file()` — reads `.sql` files, strips comments
  - `load_ml_features()` — canonical ML-ready feature query

- **Executable scripts** (`scripts/`):
  - `build_university_db.py` — idempotent DB builder
  - `export_student_report.py` — DB → ML feature CSV

- **Documentation** (`docs/DATABASE.md`):
  - Entity-Relationship Diagram (ASCII)
  - Constraint catalog
  - Query catalog
  - Build & export workflow

- **Tests** (`tests/test_db_layer.py`, `tests/test_query_layer.py`):
  - 19 new tests covering connection, execution, and querying

### Added — Documentation

- `ARCHITECTURE.md` — Architecture Decision Record (ADR)
  - Why Python config over JSON
  - Why 8 layers over single utilities module
  - Why inline storage over separate database folder
  - Why defensive programming over enforced call ordering

- `README.md` — expanded to cover both units (378 lines)

### Testing

- Test count: 42 → **61** (19 new tests for Unit 2)

### Commits in this release

- `af0a7a0` docs: expand README with Unit 2
- `fb2c0e5` feat(db): add University Training Database + SQL layer
- `22525b7` docs: add Architecture Decision Record (ADR)
- `5ce664f` test: document defensive behavior of clean_data

---

## [1.0.0] — 2025-10-04

### Added — Unit 1: Data Engineering Fundamentals

- **9-stage ETL pipeline**:
  - LOAD → VALIDATE SCHEMA → CONVERT TYPES → CLEAN
  - → VALIDATE FINAL → SAVE CSV → SAVE SQLite → QUALITY REPORT

- **8 modular layers** (`src/`):
  - `config.py` — centralized, immutable configuration
  - `logging_setup.py` — rotating file + console logging
  - `io_layer.py` — CSV loading and saving
  - `transform_layer.py` — type conversion and cleaning
  - `validate_layer.py` — schema + business rule validation
  - `storage_layer.py` — SQLite persistence with indexes
  - `report_layer.py` — data quality reporting
  - `orchestrator.py` — pipeline coordination

- **CLI** (`main.py`):
  - 5 flags: `--raw`, `--output`, `--db`, `--verbose`, `--no-verify`
  - 5 exit codes: 0 (success), 1 (unexpected), 2 (file not found),
    3 (validation error), 130 (interrupted)

- **Test suite** (`tests/`): 42 tests covering all layers

- **Containerization**: `Dockerfile` with multi-stage build

- **CI**: `.github/workflows/pipeline.yml` (GitHub Actions)

- **Documentation**: `README.md`

### Design principles applied

- Single Responsibility Principle (8 layers)
- Immutability (every transformer copies)
- Fail Fast (validate at earliest boundary)
- Error Accumulation (collect all errors, then raise)
- Exception Chaining (`raise ... from`)
- Idempotency (safe to re-run)
- Full type hints

---

## Version History Summary

| Version | Date | Focus | Tests | Files |
|---|---|---|---|---|
| **2.0.0** | 2025-10-04 | Unit 2: Database + SQL | 61 | 41 |
| 1.0.0 | 2025-10-04 | Unit 1: ETL pipeline | 42 | 28 |

---

## Links

- [Repository](https://github.com/USERNAME/student-data-pipeline)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)