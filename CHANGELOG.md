# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.0.0-dev] — Phase A — 2026-10-08
### Added

#### Feature Engineering Layer (Phase A)

- **`src/features/engineering.py`** — `FeatureEngineer` class
  - 6 engineered features:
    - `attendance_rate` (Unit 6, p. 37)
    - `academic_risk_score` (Unit 6, p. 51)
    - `score_change` (Unit 3, pp. 36-38)
    - `city_rank` (Unit 3, p. 33) — from TRAIN peers only
    - `city_score_gap` — design extension
    - `performance_level` (Unit 3, p. 19)
  - Strict **Data Leakage Prevention** (Unit 9, pp. 76-77):
    - Split TRAIN/TEST first
    - Statistics computed from TRAIN ONLY
    - City features from TRAIN peers only
  - Idempotent (`random_state=42`)

- **`src/features/__init__.py`** — PEP 562 lazy imports

- **`tests/test_features.py`** — 22 new tests
  - 3 leakage-prevention tests
  - 1 idempotency test
  - Full public API coverage

- **`docs/FEATURE_STORE.md`** — Architecture + traceability

### Changed

- **`.gitignore`**: use recursive glob (`**/*.csv`) for processed outputs
  - Fixes: `data/processed/*/file.csv` was previously tracked

### Curriculum Coverage

- Unit 3: LAG, RANK, CASE
- Unit 4: Grain, Star Schema
- Unit 6: Vectorization
- Unit 9: Data Leakage Prevention
- Unit 10: Idempotency
- Guide Ch 4: Parquet; Ch 8: Grain

### Test Count

- v3.0.0: 140 passed
- v4.0.0-dev (Phase A): **162 passed** (+22)

### Baseline

`b8a1a73`

---

## [3.0.0] - 2026-10-06

### Added

#### Multi-Source Pipeline Architecture (Unit 8)

- **5 independent source pipelines**:
  - `pipelines/csv_pipeline.py` — CSV source
  - `pipelines/sqlite_pipeline.py` — SQLite source
  - `pipelines/postgres_pipeline.py` — PostgreSQL source
  - `pipelines/mongodb_pipeline.py` — MongoDB source
  - `pipelines/json_pipeline.py` — JSON source

- **`pipelines/base_pipeline.py`** — Abstract `BasePipeline` class
  - Template Method Pattern for `run()` lifecycle
  - `STANDARD_COLUMNS` (6 standard columns)
  - `_standardize()` helper for schema consistency

- **`pipelines/run_all_pipelines.py`** — Runner for all 5 pipelines
- **`pipelines/compare_pipelines.py`** — Cross-source comparison report

#### MongoDB Integration (Unit 8)

- `src/mongo_layer.py` — Reusable MongoDB CRUD + aggregations
- `scripts/build_mongodb.py` — Idempotent MongoDB database builder
- `scripts/mongodb_read.py` — Read operations demo (11 queries)
- `scripts/mongodb_update.py` — Update/delete demo
- `scripts/mongodb_pipeline.py` — MongoDB → CSV pipeline
- Database: `University_Ai.students` (10 documents)
- Collections: `students`, `validated_students`
- Indexes: `student_id` (unique), `personal.city`, `academic.gpa`
- JSON Schema validation on `validated_students`

#### Environment & Validation

- `scripts/check_environment.py` — Full environment verification
  - Python + packages check
  - MongoDB + PostgreSQL services check
  - Data files check
  - Pipeline modules check

#### Documentation

- `docs/PIPELINE_ARCHITECTURE.md` — Comprehensive multi-source architecture
- `docs/MONGODB.md` — MongoDB integration guide
- `database/mongodb/README.md` — MongoDB schema + design decisions
- `database/mongodb/queries.md` — MongoDB query catalog

### Changed

- **Output structure**: `data/processed/{source}/{source}_clean.csv`
  - Previously: single output file
  - Now: 5 separate outputs, one per source

- **Comparison layer**: `data/comparison/` for cross-source analysis
  - `comparison_report.md` — human-readable report
  - `comparison_data.csv` — machine-readable data

- **`ARCHITECTURE.md`** — Updated to v3.0.0 with multi-source architecture

### Fixed

- **Float→Int64 cast error** in SQLite/PostgreSQL pipelines
  - Root cause: `pd.to_numeric().astype("Int64")` on float values
  - Solution: `.round().astype("Int64")` before conversion

- **Idempotency**: `build_mongodb.py` drops collection before re-insert

- **`pipelines/README.md`** — Fixed filename typo (was `READE.md`)

### Infrastructure

- 5 pipelines tested end-to-end
- 61 unit tests passing
- Environment check script
- GitHub Actions CI workflow

### Statistics

| Metric | Value |
|--------|-------|
| Data sources | 5 |
| Total rows processed | 37 (8+8+8+10+3) |
| Total runtime | ~0.63 seconds |
| Python modules | 11 (was 10) |
| Pipelines | 5 (was 0) |
| Tests | 61 |
| Documentation files | 7 (was 5) |

### Pipeline Comparison Results

| Source | Rows | Columns | Missing |
|--------|------|---------|---------|
| CSV | 8 | 6 | 0 |
| SQLite | 8 | 6 | 16 |
| PostgreSQL | 8 | 6 | 16 |
| MongoDB | 10 | 6 | 0 |
| JSON | 3 | 6 | 0 |

**Note:** The 16 missing values in SQLite/PostgreSQL are **not a bug** — they accurately reflect source schemas (no `attendance` column).

### Commits in this release

- `b02f52d` docs(pipelines): fix README filename typo
- `2d6cbf1` chore(release): prepare v3.0.0
- `9fe6660` feat(pipelines): add JSON pipeline + environment check (Unit 8)
- `343c99a` feat(pipelines): add 4 independent source pipelines (Unit 8)
- `e5acf97` chore: update comparison report with latest pipeline run

---

## [2.0.0] - 2025-10-04

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

- **PostgreSQL support**:
  - `database/queries/postgresql/` — 13 SQL files
  - `docs/POSTGRESQL_SETUP.md` — step-by-step setup guide

- **Tests** (`tests/test_db_layer.py`, `tests/test_query_layer.py`):
  - 19 new tests covering connection, execution, and querying

### Added — Documentation

- `ARCHITECTURE.md` — Architecture Decision Record (ADR)
  - Why Python config over JSON
  - Why modular layers over single utilities module
  - Why inline storage over separate database folder
  - Why defensive programming over enforced call ordering

- `README.md` — expanded to cover both units

### Testing

- Test count: 42 → **61** (19 new tests for Unit 2)

### Commits in this release

- `af0a7a0` docs: expand README with Unit 2
- `fb2c0e5` feat(db): add University Training Database + SQL layer
- `22525b7` docs: add Architecture Decision Record (ADR)
- `5ce664f` test: document defensive behavior of clean_data

---

## [1.0.0] - 2025-10-04

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

### Commits in this release

- `91d0d50` feat: initial production-grade data engineering pipeline
- `d4fc472` chore(release): prepare v2.0.0 (initial tag)

---

## Version History Summary

| Version | Date | Focus | Tests | Pipelines |
|---------|------|-------|-------|-----------|
| **3.0.0** | 2026-10-06 | Multi-Source Pipelines (Unit 8) | 61 | 5 |
| 2.0.0 | 2025-10-04 | Unit 2: Database + SQL | 61 | 0 |
| 1.0.0 | 2025-10-04 | Unit 1: ETL Pipeline | 42 | 0 |

---

## Roadmap

### Planned for v4.0.0

- Unit 4: Database Design (ERD, Normalization)
- Unit 5: Python for Data Engineering (multi-source ETL)
- Unit 6: Pandas / Polars performance
- Unit 7: APIs & Web Scraping
- Unit 9: Data Quality
- Streamlit Dashboard
- Pre-commit hooks (black + ruff + pytest)

### Considered

- Incremental loading (watermark columns)
- Schema evolution handling
- Parallel pipeline execution (`concurrent.futures`)
- SQL Server integration
- Cloud databases (AWS RDS, Azure)

---

## Links

- [Repository](https://github.com/GalalAlghaberi/student-data-pipeline)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)