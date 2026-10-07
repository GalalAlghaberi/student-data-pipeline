# Student Data Engineering Pipeline

> End-to-end data engineering pipeline that transforms raw student data
> from 5 sources into ML-ready datasets — with validation, quality
> checks, and multi-database support.

**Version:** v4.0.0-dev (current: v3.0.0)  
**Python:** 3.14.7 · **OS:** Windows 11  
**Databases:** SQLite 3.50.4 · PostgreSQL 18.6 · MongoDB 7.0.14

[![Tests](https://img.shields.io/badge/tests-61%20passed-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![GitHub](https://img.shields.io/badge/GitHub-Public-success)](https://github.com/GalalAlghaberi/student-data-pipeline)

---

## 📋 جدول المحتويات

1. [Overview](#overview)
2. [Curriculum Alignment](#curriculum-alignment)
3. [Architecture](#architecture)
4. [Project Structure](#project-structure)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Data Sources](#data-sources)
8. [Data Quality](#data-quality)
9. [Testing](#testing)
10. [Documentation](#documentation)
11. [Roadmap](#roadmap)
12. [Author](#author)

---

## Overview

This project implements a **multi-source data engineering pipeline** that:

- **Extracts** data from 5 different sources (CSV, JSON, SQLite, PostgreSQL, MongoDB)
- **Transforms** and **cleans** data using Pandas + NumPy
- **Validates** data quality using 61 automated tests
- **Loads** cleaned data to databases and Parquet (v4)
- **Produces** ML-ready datasets for analytics and machine learning

### 🎯 Project Goals

1. Build reliable, reproducible data pipelines
2. Enforce strict data quality at every stage
3. Support multiple database backends
4. Produce ML-ready features with documented lineage
5. Follow software engineering best practices

---

## 🗺️ Curriculum Alignment

This project is aligned with **two complementary references**:

### 1. Course 3 — Data Engineering & Databases for AI

| Unit | Topic | Status |
|------|-------|--------|
| 1 | Data Engineering Fundamentals | ✅ Complete |
| 2 | Relational DB & SQL | ✅ Complete |
| 3 | Advanced SQL | ✅ Complete |
| 4 | Database Design & Normalization | ✅ Complete |
| 5 | Python for Data Engineering | ✅ Complete |
| 6 | Pandas / NumPy / Polars | ✅ Complete |
| 7 | APIs & Web Scraping | 🔄 v4 |
| 8 | MongoDB & NoSQL | ✅ Complete |
| 9 | Data Cleaning & Quality | ✅ Complete |
| 10 | ETL/ELT Pipelines | ✅ Complete |
| 11 | Git / GitHub / Documentation | ✅ Complete |

### 2. Guide — مهارات ومبادئ هندسة البيانات

| Ch | Topic | Status |
|----|-------|--------|
| 1 | مفهوم DE + الأهداف | ✅ |
| 2 | بنية المشاريع | ✅ |
| 3 | Architecture First | ✅ |
| 4 | استراتيجيات التخزين | 🔄 v4 |
| 5 | الحوسبة والموارد | ⏳ v4 |
| 6 | OLTP vs OLAP | ✅ |
| 7 | DW + Star Schema | 🔄 v4 |
| 8 | نمذجة البيانات + Grain | ✅ |
| 9 | جودة البيانات | ✅ |
| 10 | CI/CD + Docker | ✅ |
| 11 | Unit Testing | ✅ |
| 12 | المبدأ الجوهري | ✅ |

### 📖 Full Curriculum Map

For the complete mapping between Units and Chapters, see:

- **[docs/CURRICULUM_MAP.md](docs/CURRICULUM_MAP.md)** — detailed cross-reference
- **[docs/ARCHITECTURE_LAYERS.md](docs/ARCHITECTURE_LAYERS.md)** — OLTP/OLAP/ML layers

### 🎯 Core Principle

> "Facilitating the movement, storage, and access to data in a
> **repeatable**, **resilient**, and **scalable** manner."
>
> — دليل مهارات ومبادئ هندسة البيانات (Ch 12)

---

## Architecture

### Three-Layer Model

```
┌──────────────────────────────────────────────────────────┐
│  BRONZE (Raw)      data/bronze/                          │
│  ├── csv_raw/      5 source files preserved              │
│  ├── api_raw/                                            │
│  └── mongo_raw/                                          │
└────────────────────┬─────────────────────────────────────┘
                     │ Clean + Validate
                     ▼
┌──────────────────────────────────────────────────────────┐
│  SILVER (Cleaned)  data/silver/                          │
│  └── *_clean.csv   (5 pipelines, 37 rows)                │
└────────────────────┬─────────────────────────────────────┘
                     │ Star Schema + Features
                     ▼
┌──────────────────────────────────────────────────────────┐
│  GOLD (Analytics)  data/gold/                            │
│  ├── fact_student_performance.parquet                    │
│  ├── dim_*.parquet                                       │
│  └── ml_features.parquet                                 │
└────────────────────┬─────────────────────────────────────┘
                     │ Train / Predict
                     ▼
┌──────────────────────────────────────────────────────────┐
│  ML MODEL          models/                               │
│  └── model_metrics.csv                                   │
└──────────────────────────────────────────────────────────┘
```

For detailed layer documentation, see **[docs/ARCHITECTURE_LAYERS.md](docs/ARCHITECTURE_LAYERS.md)**.

### Multi-Source Pipelines (v3.0.0)

| Source | Rows In | Rows Out | Duration |
|--------|---------|----------|----------|
| CSV | 8 | 8 | 0.02s |
| SQLite | 8 | 8 | 0.03s |
| PostgreSQL | 8 | 8 | 0.40s |
| MongoDB | 10 | 10 | 0.19s |
| JSON | 3 | 3 | 0.01s |
| **Total** | **37** | **37** | **~0.6s** |

---

## Project Structure

```
student_data_pipeline/
├── pipelines/                     ⭐ v3.0.0
│   ├── base_pipeline.py           # Abstract base class
│   ├── csv_pipeline.py
│   ├── sqlite_pipeline.py
│   ├── postgres_pipeline.py
│   ├── mongodb_pipeline.py
│   ├── json_pipeline.py
│   ├── api_pipeline.py            🆕 v4
│   ├── scraper_pipeline.py        🆕 v4
│   ├── run_all_pipelines.py
│   └── compare_pipelines.py
│
├── src/                            # 11 modules
│   ├── config.py                  # version = "4.0.0"
│   ├── logging_setup.py
│   ├── io_layer.py
│   ├── transform_layer.py
│   ├── validate_layer.py
│   ├── storage_layer.py
│   ├── report_layer.py
│   ├── orchestrator.py
│   ├── db_layer.py
│   ├── query_layer.py
│   ├── mongo_layer.py
│   ├── warehouse/                 🆕 v4
│   │   ├── parquet_writer.py
│   │   └── star_schema.py
│   ├── features/                  🆕 v4
│   │   └── engineering.py
│   └── ml/                        🆕 v4
│       ├── split.py
│       ├── baseline.py
│       ├── trainer.py
│       └── metrics.py
│
├── data/
│   ├── bronze/                    🆕 v4 — Raw
│   ├── silver/                    🆕 v4 — Cleaned
│   ├── gold/                      🆕 v4 — Parquet
│   ├── raw/                       # Legacy (v3.0.0)
│   ├── processed/                 # Legacy (v3.0.0)
│   └── comparison/
│
├── database/
│   ├── schema.sql
│   ├── seed_data.sql
│   ├── queries/                   # SQL queries by topic
│   └── mongodb/
│
├── docs/                           # 9 files
│   ├── CURRICULUM_MAP.md          🆕 v4
│   ├── ARCHITECTURE_LAYERS.md     🆕 v4
│   ├── MEDALLION.md               🆕 v4
│   ├── FEATURE_STORE.md           🆕 v4
│   ├── DATABASE.md
│   ├── POSTGRESQL_SETUP.md
│   ├── MONGODB.md
│   └── PIPELINE_ARCHITECTURE.md
│
├── tests/                          # 61 tests
│   ├── test_io.py (8)
│   ├── test_transform.py (13)
│   ├── test_validate.py (10)
│   ├── test_storage.py (6)
│   ├── test_orchestrator.py (5)
│   ├── test_db_layer.py (10)
│   ├── test_query_layer.py (9)
│   └── test_warehouse.py          🆕 v4
│
├── scripts/                        # 9+ scripts
│   ├── build_university_db.py
│   ├── export_student_report.py
│   ├── run_sql_file.py
│   ├── build_mongodb.py
│   ├── check_environment.py
│   ├── benchmark.py               🆕 v4
│   └── run_ml_pipeline.py         🆕 v4
│
├── main.py
├── requirements.txt
├── pytest.ini
├── Dockerfile
├── Makefile                       🆕 v4
├── .github/workflows/pipeline.yml
├── README.md                      (this file)
├── ARCHITECTURE.md
└── CHANGELOG.md
```

---

## Installation

### Prerequisites

- Python 3.14.7+
- SQLite 3.50.4+
- PostgreSQL 18.6 (optional)
- MongoDB 7.0.14 (optional)

### Quick Start

```bash
# 1. Clone
git clone git@github.com:GalalAlghaberi/student-data-pipeline.git
cd student-data-pipeline

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify environment
python scripts/check_environment.py
```

### Environment Variables

Create `.env` (do NOT commit):
```env
PG_PASSWORD=your_postgres_password
MONGO_URI=mongodb://localhost:27017/
```

See `.env.example` for the full template.

---

## Usage

### Run all pipelines

```bash
python pipelines/run_all_pipelines.py
```

### Compare results

```bash
python pipelines/compare_pipelines.py
cat data/comparison/comparison_report.md
```

### Run MongoDB demos

```bash
python scripts/build_mongodb.py
python scripts/mongodb_read.py
python scripts/mongodb_update.py
```

### Run tests

```bash
python -m pytest tests/ -v
```

### v4 — Build Gold Layer

```bash
# Build OLAP + ML features
python -m src.warehouse.star_schema
python -m src.features.engineering

# Train model
python scripts/run_ml_pipeline.py
```

### v4 — Makefile shortcuts

```bash
make pipeline    # Run all pipelines
make test        # Run all tests
make ml          # Train ML model
make docker      # Build + run Docker
```

---

## Data Sources

| Source | Type | Location | Purpose |
|--------|------|----------|---------|
| CSV | Tabular | `data/bronze/csv_raw/` | Training data |
| JSON | Semi-structured | `data/bronze/json_raw/` | API simulation |
| SQLite | Relational | `data/raw/university.db` | OLTP simulation |
| PostgreSQL | Relational | `localhost:5432` | Production sim |
| MongoDB | Document | `localhost:27017` | NoSQL simulation |
| REST API | Web | *(v4)* | Live acquisition |
| Web Scraping | HTML | *(v4)* | Fallback source |

---

## Data Quality

### Quality Rules

| Field | Rule |
|-------|------|
| `student_id` | Unique, not null |
| `name` | Not null |
| `age` | 16 ≤ age ≤ 80 |
| `gpa` | 0 ≤ gpa ≤ 4 |
| `attendance` | 0 ≤ attendance ≤ 100 |
| `city` | Not null |

### Quality Dimensions

Following Unit 9 + Guide Ch 9:

- **Accuracy** — is the value correct?
- **Completeness** — is data present?
- **Consistency** — same representation?
- **Validity** — within rules?
- **Uniqueness** — no duplicates?
- **Timeliness** — current enough?

### Quality Report

Generated at `data/comparison/comparison_report.md`:

```
Input Rows:      37
Output Rows:     37
Rejected Rows:   0
Missing Values:  32 (SQLite/Postgres — expected)
Validation:      PASSED
```

---

## Testing

```bash
python -m pytest tests/ -q
# 61 passed in 1.4s
```

### Test Coverage

| Layer | Tests |
|-------|-------|
| I/O | 8 |
| Transform | 13 |
| Validate | 10 |
| Storage | 6 |
| Orchestrator | 5 |
| Database | 10 |
| Query | 9 |
| **Total** | **61** |

### v4 Additions

- `tests/test_warehouse.py` — Parquet + Star Schema
- `tests/test_features.py` — Feature Engineering
- `tests/test_ml.py` — Model training

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | This file |
| `ARCHITECTURE.md` | ADR — architectural decisions |
| `CHANGELOG.md` | Version history |
| `docs/CURRICULUM_MAP.md` | 🆕 Units ↔ Chapters mapping |
| `docs/ARCHITECTURE_LAYERS.md` | 🆕 OLTP/OLAP/ML layers |
| `docs/DATABASE.md` | ERD + schema |
| `docs/POSTGRESQL_SETUP.md` | PostgreSQL guide |
| `docs/MONGODB.md` | MongoDB guide |
| `docs/PIPELINE_ARCHITECTURE.md` | Multi-source design |
| `docs/MEDALLION.md` | 🆕 Bronze/Silver/Gold |
| `docs/FEATURE_STORE.md` | 🆕 Feature catalog |

---

## Roadmap

### ✅ v3.0.0 (Current)
- 5 independent pipelines
- 61 automated tests
- Multi-database support
- Complete documentation

### 🔄 v4.0.0 (In Progress)
- [ ] **Phase 1:** API + Scraper pipelines (Unit 7)
- [ ] **Phase 2:** Parquet writer + Star Schema (Ch 4, 7)
- [ ] **Phase 3:** Medallion Architecture (Bronze/Silver/Gold)
- [ ] **Phase 4:** Feature Engineering layer (Unit 9)
- [ ] **Phase 5:** ML Integration (split + baseline + trainer)
- [ ] **Phase 6:** CI/CD + Docker + Makefile
- [ ] **Phase 7:** Release v4.0.0

**Timeline:** ~20 working days

### 🎯 v5.0.0 (Planned)
- Airflow / Dagster orchestration
- MLflow tracking
- dbt transformations
- Streamlit dashboard

---

## Related References

- **Course 3:** Data Engineering & Databases for AI (Units 1–11)
- **Guide:** مهارات ومبادئ هندسة البيانات (12 chapters)
- **ML:** Applied ML Day 1 (California Housing)

---

## Author

**Galal Al-Ghaberi**  
Mechatronics Engineer · University of Dhamar  
📧 galalalghaberi@gmail.com  
📱 +967 777273715  
🔗 [GitHub](https://github.com/GalalAlghaberi)

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

**Last Updated:** 2026-10-07  
**Version:** v4.0.0-dev  
**Status:** Active Development