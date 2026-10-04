# Architecture Decision Record (ADR)

> **Why this structure, not another.**

This document explains the **architectural decisions** made in this project, and why we deviated from the textbook structure suggested in standard Data Engineering study guides.

---

## Table of Contents

1. [Philosophy](#philosophy)
2. [Project Structure Decision](#project-structure-decision)
3. [Config: Python module vs JSON file](#config-python-module-vs-json-file)
4. [Layers vs single utilities module](#layers-vs-single-utilities-module)
5. [Storage: inline vs separate database folder](#storage-inline-vs-separate-database-folder)
6. [Safety: defensive programming](#safety-defensive-programming)
7. [Testing strategy](#testing-strategy)
8. [Summary table](#summary-table)

---

## Philosophy

> "Architecture First — اتخاذ القرارات المعمارية الكبرى قبل كتابة أي سطر برمجي."

Every architectural decision in this project answers **one question**:

**Does this make the code more maintainable, testable, or resilient?**

If not, it does not belong here.

---

## Project Structure Decision

### What the study guide suggests

```
my_data_pipeline_project/
|-- README.md
|-- Dockerfile
|-- docker-compose.yaml
|-- requirements.txt
|-- main.py
|-- tests/
|   |-- conftest.py
|   `-- test_pipeline.py
|-- configs/
|   `-- configurations.json
|-- utilities/
|   `-- general_functions.py
|-- database/
|   `-- run_database.py
`-- sample_data/
    `-- data_file.csv
```

### What we built

```
student_data_pipeline/
|-- data/
|   |-- raw/students_raw.csv
|   |-- processed/.gitkeep
|   `-- student_data.db
|-- logs/
|   `-- .gitkeep
|-- src/
|   |-- __init__.py
|   |-- config.py
|   |-- logging_setup.py
|   |-- io_layer.py
|   |-- transform_layer.py
|   |-- validate_layer.py
|   |-- storage_layer.py
|   |-- report_layer.py
|   `-- orchestrator.py
|-- tests/
|   |-- conftest.py
|   |-- test_io.py
|   |-- test_transform.py
|   |-- test_validate.py
|   |-- test_storage.py
|   `-- test_orchestrator.py
|-- legacy/
|   `-- main_v1.py
|-- main.py
|-- requirements.txt
|-- pytest.ini
|-- Dockerfile
|-- .gitignore
`-- README.md
```

### Why the difference?

The guide's structure is a **template from a first project**. Ours is an **evolution of that template** based on real engineering principles:

| Aspect | Guide | Ours | Winner |
|--------|-------|------|--------|
| Layers | 3 (utilities, database, configs) | 8 (one per responsibility) | Ours |
| Config | JSON | Python with `Final` | Ours |
| Tests | 1 file | 6 files (one per layer) | Ours |
| Type safety | None | Complete | Ours |
| CI | Not mentioned | GitHub Actions | Ours |

**We did not abandon the guide. We evolved it.**

---

## Config: Python module vs JSON file

### Guide suggestion

```json
{
  "pipeline": {
    "raw_file": "data/raw/students_raw.csv",
    "output_file": "data/processed/students_ml_ready.csv"
  }
}
```

### Our decision

```python
# src/config.py
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
RAW_FILE: Final[Path] = PROJECT_ROOT / "data" / "raw" / "students_raw.csv"

REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset(
    {"student_id", "name", "age", "gpa", "attendance", "city"}
)
```

### Why Python over JSON?

| Criterion | JSON | Python module |
|-----------|------|---------------|
| Type hints | No | Yes (`Final[...]`) |
| IDE autocomplete | Limited | Full |
| Computed values | No | Yes (`Path(__file__)`) |
| Validation at import | No | Yes (frozen sets, ranges) |
| Refactoring safety | Manual | Automated by tools |
| Immutable by default | No | Yes (`Final`) |

### Can we get both?

Yes. We can later add **external JSON overrides**:

```python
# Future: config.py
import json
EXTERNAL_CONFIG = Path("configs/overrides.json")
if EXTERNAL_CONFIG.exists():
    overrides = json.loads(EXTERNAL_CONFIG.read_text())
    RAW_FILE = Path(overrides.get("raw_file", RAW_FILE))
```

**This gives the best of both worlds: type-safe defaults + external override.**

---

## Layers vs single utilities module

### Guide suggestion

```
utilities/
`-- general_functions.py   # all helpers in one file
```

### Our decision

```
src/
|-- io_layer.py             # load/save CSV
|-- transform_layer.py      # type conversion + cleaning
|-- validate_layer.py       # schema + data validation
|-- storage_layer.py        # SQLite persistence
|-- report_layer.py         # quality report
`-- orchestrator.py         # pipeline coordination
```

### Why split them?

**Single Responsibility Principle (SRP)** — from SOLID:

> A module should have **one reason to change**.

| Aspect | general_functions.py | 8 layers |
|--------|---------------------|----------|
| File size | Will exceed 500 lines | Each under 200 |
| Reason to change | Many | One per layer |
| Test isolation | Hard | Trivial |
| Onboarding time | Long | Short |
| God-object risk | High | Zero |

### Concrete benefit

When we discovered that `clean_data` crashed on non-numeric columns, **the fix touched only `transform_layer.py`** — no other layer needed review.

If it had been in `general_functions.py`, we'd have had to re-test the whole module.

---

## Storage: inline vs separate database folder

### Guide suggestion

```
database/
`-- run_database.py
```

### Our decision

```python
# src/storage_layer.py
def save_to_sqlite(df, db_file, table_name="students", create_indexes=True):
    _assert_safe_identifier(table_name)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_file) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        ...
```

### Why inline for now?

**YAGNI — You Aren't Gonna Need It.**

- We currently use **SQLite only** (built-in with Python).
- No connection pooling, migrations, or clustering required.
- The whole persistence fits in one 60-line file.

### When would we split?

When **one** of these becomes true:

1. We add **PostgreSQL** or **another database**.
2. We need **migrations** (Alembic, Django ORM).
3. We need **connection pooling** (SQLAlchemy).
4. We need **repository pattern** with multiple implementations.

**Then** we create:

```
src/
|-- repositories/
|   |-- __init__.py
|   |-- base.py
|   |-- student_repository.py       # abstract
|   |-- sqlite_student_repository.py
|   `-- postgres_student_repository.py
```

**We do not pre-build for problems we do not have.**

---

## Safety: defensive programming

### The incident

During testing, `clean_data` crashed when called **without** `convert_data_types`:

```
TypeError: '>=' not supported between instances of 'str' and 'int'
```

### Two possible fixes

**Fix A: Enforce call order** (guide's suggestion)

```python
def clean_data(df):
    if not pd.api.types.is_numeric_dtype(df["age"]):
        raise ValueError("Call convert_data_types first")
    ...
```

**Fix B: Defensive skip** (our choice)

```python
def _handle_outliers(df):
    for col, (lo, hi) in OUTLIER_RANGES.items():
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning("Column '%s' is not numeric; skipping.", col)
            continue
        ...
```

### Why Fix B is better

| Aspect | Fix A | Fix B |
|--------|-------|-------|
| Coupling | High (order matters) | Low (independent) |
| Testability | Must call two functions | Can test each alone |
| Robustness | Brittle | Resilient |
| Debugging | Silent failure | Explicit warning |
| Documented | No | Yes (`TestDefensiveBehavior`) |

### The principle

> **Each function must be safe by default, not dependent on strict call ordering.**

This is documented **in code** (`test_transform.py::TestDefensiveBehavior`) and **in Git** (commit `5ce664f`).

---

## Testing strategy

### Guide suggestion

```
tests/
|-- conftest.py
`-- test_pipeline.py   # one file
```

### Our decision

```
tests/
|-- conftest.py                     # shared fixtures
|-- test_io.py                      # 8 tests
|-- test_transform.py               # 13 tests
|-- test_validate.py                # 10 tests
|-- test_storage.py                 # 6 tests
`-- test_orchestrator.py            # 5 tests
```

### Why split?

1. **Parallel execution**: pytest runs them faster.
2. **Isolation**: a failing I/O test does not hide a failing transform test.
3. **Maintenance**: when changing `validate_layer.py`, only run `test_validate.py`.
4. **Coverage reports**: per-layer metrics are meaningful.

### Testing categories we cover

| Category | Example | File |
|----------|---------|------|
| Unit | `test_converts_strings_to_numeric` | `test_transform.py` |
| Edge cases | `test_raises_on_empty_csv` | `test_io.py` |
| Idempotency | `test_idempotent` | `test_transform.py` |
| Purity | `test_does_not_mutate_input` | `test_transform.py` |
| Security | `test_rejects_unsafe_table_name` | `test_storage.py` |
| Integration | `test_runs_successfully` | `test_orchestrator.py` |
| CLI | `test_returns_2_on_missing_file` | `test_orchestrator.py` |
| Design contract | `TestDefensiveBehavior` | `test_transform.py` |

---

## Summary table

| Decision | Guide's suggestion | Our choice | Reason |
|----------|-------------------|------------|--------|
| Structure | 3 subfolders | 8 layers | SRP |
| Config | JSON | Python with `Final` | Type safety |
| Utilities | One file | 6 layer files | Testability |
| Database | `database/` folder | `storage_layer.py` | YAGNI |
| Safety | Enforce call order | Defensive skip | Resilience |
| Tests | 1 file | 6 files | Isolation |
| CI | Not mentioned | GitHub Actions | Automation |

---

## Principles we share with the guide

- **Architecture First** — decided the structure before writing code
- **Main entry point** — `main()` + `if __name__ == "__main__"`
- **Data flow order** — load → transform → validate → save
- **Unit testing** — mandatory, not optional
- **CI/CD** — automated pipelines
- **The Unifying Principle** — repeatable, resilient, scalable

---

## Principles where we go further

- **Type hints** on every function signature
- **Exception chaining** (`raise ... from exc`)
- **Dataclasses** for structured returns
- **Rotating logs** with console mirroring
- **CLI with exit codes** for automation
- **Defensive programming** with explicit warnings
- **Idempotency** as a design invariant

---

## When to revisit this document

Revisit these decisions when:

1. Adding a **second database** (e.g., PostgreSQL)
2. Adding a **new data source** (API, Kafka)
3. **Deploying to production** at scale
4. Onboarding **new team members**
5. Conducting a **post-mortem** after an incident

---

## Final word

> We did not abandon the guide.
> We applied its **spirit** — not its **letter**.

Every deviation is a **considered decision** backed by a principle, documented, and tested.

---

**Author:** Student Data Engineering Pipeline Team
**Version:** 2.0.0
**Last updated:** 2025
**Related files:**
- `README.md` — how to use the project
- `tests/test_transform.py::TestDefensiveBehavior` — design contract
- Git history — `feat:` and `test:` commits