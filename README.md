# Student Data Engineering Pipeline

> **End-to-End Data Engineering Pipeline** — from raw student CSV to a validated, cleaned, ML-ready dataset, with SQLite persistence, quality reporting, and full test coverage.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/pandas-2.2%2B-green)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-39%20passed-brightgreen)](#testing)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](#license)

---

## Overview

This project transforms **raw student data** into a **clean, validated, ML-ready dataset**. It demonstrates production-grade practices for a Data Engineering pipeline:

- Explicit **9-stage ETL** architecture
- Dual storage (**CSV** + **SQLite** with indexes)
- Multi-layer **validation** (schema, business rules, uniqueness, ranges)
- **Rotating logs** + console output
- **Type hints** and **docstrings** everywhere
- Full **test suite** with pytest (39 tests)
- **Docker** and **CI** ready

---

## Architecture

```
                RAW CSV
                    |
                    v
            [1] LOAD             io_layer.load_data
                    |
                    v
            [2] VALIDATE SCHEMA  validate_layer.validate_schema   (Guard)
                    |
                    v
            [3] CONVERT TYPES    transform_layer.convert_data_types
                    |
                    v
            [4] CLEAN            transform_layer.clean_data
                    |
                    v
            [5] VALIDATE FINAL   validate_layer.validate_data     (Guard)
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

---

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Test

```bash
pytest tests/ -v
```

### Docker

```bash
docker build -t student-pipeline .
docker run --rm -v $(pwd)/data:/app/data student-pipeline
```

---

## CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| --raw | -r | data/raw/students_raw.csv | Input CSV path |
| --output | -o | data/processed/students_ml_ready.csv | Output CSV path |
| --db | -d | data/student_data.db | SQLite path |
| --verbose | -v | off | Enable DEBUG logging |
| --no-verify | — | off | Skip post-save verification |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Unexpected error |
| 2 | File not found |
| 3 | Validation error |
| 130 | Interrupted (Ctrl+C) |

---

## Project Layout

```
student_data_pipeline/
|-- data/
|   |-- raw/                     # immutable input
|   |-- processed/               # generated output
|   `-- student_data.db          # SQLite database
|-- logs/
|   `-- pipeline.log             # rotating log (10 MB x 5)
|-- src/
|   |-- __init__.py
|   |-- config.py                # all constants
|   |-- logging_setup.py         # rotating logger
|   |-- io_layer.py              # load / save CSV
|   |-- transform_layer.py       # type conv + cleaning
|   |-- validate_layer.py        # schema + data validation
|   |-- storage_layer.py         # SQLite persistence
|   |-- report_layer.py          # quality report
|   `-- orchestrator.py          # pipeline coordinator
|-- tests/
|   |-- conftest.py              # shared fixtures
|   |-- test_io.py
|   |-- test_transform.py
|   |-- test_validate.py
|   |-- test_storage.py
|   `-- test_orchestrator.py
|-- legacy/
|   `-- main_v1.py               # original educational version
|-- main.py                      # CLI entry point
|-- requirements.txt
|-- pytest.ini
|-- Dockerfile
|-- .gitignore
`-- README.md
```

---

## Data Quality Rules

| Rule | Constraint |
|------|------------|
| student_id | Unique, non-null, integer |
| name | Non-null |
| age | Between 16 and 80 |
| gpa | Between 0 and 4 |
| attendance | Between 0 and 100 |
| city | Filled with "Unknown" if missing |

### Missing-Value Policy

| Column | Policy |
|--------|--------|
| name | Drop row |
| city | Fill with "Unknown" |
| age | Fill with median |
| gpa | Fill with median |
| attendance | Fill with median |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Technologies

- Python 3.10+
- pandas 2.2+
- SQLite (built-in)
- pytest 8+
- Docker
- GitHub Actions

---

## License

MIT (c) 2025