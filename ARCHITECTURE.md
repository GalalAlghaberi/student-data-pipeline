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
6. [Multi-Source Pipeline Architecture (v3.0.0)](#multi-source-pipeline-architecture-v300)
7. [Safety: defensive programming](#safety-defensive-programming)
8. [Testing strategy](#testing-strategy)
9. [Summary table](#summary-table)

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

### What we built (v3.0.0)

```
student_data_pipeline/
|-- data/
|   |-- raw/
|   |   |-- students_raw.csv          # Unit 1 input
|   |   |-- students_raw.json         # Unit 8 input
|   |   `-- university.db             # Unit 2 SQLite
|   |-- processed/
|   |   |-- csv/csv_clean.csv
|   |   |-- sqlite/sqlite_clean.csv
|   |   |-- postgres/postgres_clean.csv
|   |   |-- mongodb/mongodb_clean.csv
|   |   `-- json/json_clean.csv
|   |-- comparison/
|   |   |-- comparison_report.md
|   |   `-- comparison_data.csv
|   `-- student_data.db
|-- logs/
|   `-- pipeline.log
|-- src/                               # 11 layers
|   |-- __init__.py
|   |-- config.py
|   |-- logging_setup.py
|   |-- io_layer.py
|   |-- transform_layer.py
|   |-- validate_layer.py
|   |-- storage_layer.py
|   |-- report_layer.py
|   |-- orchestrator.py
|   |-- db_layer.py
|   |-- query_layer.py
|   `-- mongo_layer.py
|-- pipelines/                         # NEW in v3.0.0
|   |-- __init__.py
|   |-- base_pipeline.py               # Abstract base class
|   |-- csv_pipeline.py
|   |-- sqlite_pipeline.py
|   |-- postgres_pipeline.py
|   |-- mongodb_pipeline.py
|   |-- json_pipeline.py
|   |-- run_all_pipelines.py
|   `-- compare_pipelines.py
|-- scripts/
|   |-- build_university_db.py
|   |-- export_student_report.py
|   |-- build_mongodb.py
|   |-- mongodb_read.py
|   |-- mongodb_update.py
|   |-- mongodb_pipeline.py
|   `-- check_environment.py
|-- tests/
|   |-- conftest.py
|   |-- test_io.py
|   |-- test_transform.py
|   |-- test_validate.py
|   |-- test_storage.py
|   |-- test_orchestrator.py
|   |-- test_db_layer.py
|   `-- test_query_layer.py
|-- docs/
|   |-- DATABASE.md
|   |-- POSTGRESQL_SETUP.md
|   |-- MONGODB.md
|   `-- PIPELINE_ARCHITECTURE.md
|-- legacy/
|   `-- main_v1.py
|-- main.py
|-- requirements.txt
|-- pytest.ini
|-- Dockerfile
|-- .gitignore
|-- ARCHITECTURE.md
|-- CHANGELOG.md
`-- README.md
```

### Why the difference?

The guide's structure is a **template from a first project**. Ours is an **evolution of that template** based on real engineering principles:

| Aspect | Guide | Ours | Winner |
|--------|-------|------|--------|
| Layers | 3 (utilities, database, configs) | 11 (one per responsibility) | Ours |
| Config | JSON | Python with `Final` | Ours |
| Tests | 1 file | 8 files (one per layer) | Ours |
| Pipelines | Not mentioned | 5 independent pipelines | Ours |
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
|-- orchestrator.py         # pipeline coordination
|-- db_layer.py             # SQLite connection + execution
|-- query_layer.py          # SQL -> DataFrame
`-- mongo_layer.py          # MongoDB CRUD + aggregations
```

### Why split them?

**Single Responsibility Principle (SRP)** — from SOLID:

> A module should have **one reason to change**.

| Aspect | general_functions.py | 11 layers |
|--------|---------------------|-----------|
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

- SQLite is built-in with Python.
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

## Multi-Source Pipeline Architecture (v3.0.0)

### The problem

By Unit 8, the project handles **five different data sources**:

| Source | Type | Tool |
|--------|------|------|
| CSV | Flat file | pandas |
| JSON | Semi-structured | pandas + json |
| SQLite | Embedded RDBMS | sqlite3 |
| PostgreSQL | Client-server RDBMS | psycopg2 |
| MongoDB | Document DB | pymongo |

**Challenge:** Each source has different schema, types, and access patterns.

### The solution: BasePipeline abstract class

```python
class BasePipeline(ABC):
    SOURCE_NAME: str = "base"
    STANDARD_COLUMNS = ["student_id", "name", "age", "gpa", "attendance", "city"]

    @abstractmethod
    def extract(self) -> pd.DataFrame: ...

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame: ...

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None: ...

    def load(self, df: pd.DataFrame) -> Path: ...   # Concrete

    def run(self) -> PipelineResult: ...             # Concrete
```

### Design patterns applied

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Template Method** | `run()` | Defines the 4-stage skeleton |
| **Abstract Factory** | `BasePipeline` | Contract for all pipelines |
| **Strategy** | 5 subclasses | Different extract/transform per source |
| **Open/Closed** | Extension point | Add source = add file, no edits |

### Why not one big pipeline?

| Criterion | Single pipeline | 5 pipelines |
|-----------|-----------------|-------------|
| Isolation | All or nothing | Failures contained |
| Comparability | Mixed logic | Same interface |
| Extensibility | Modify core | Add new file |
| Testing | Complex fixtures | Per-source tests |
| Observability | Hard to trace | Per-source metrics |

### Standardization Layer

All pipelines must output **6 standard columns**:

```
student_id | name | age | gpa | attendance | city
```

Missing columns are filled with `None`. This is what makes cross-source comparison possible.

### Result

Running all 5 pipelines takes **~0.6 seconds** and produces:

```
data/processed/csv/csv_clean.csv
data/processed/sqlite/sqlite_clean.csv
data/processed/postgres/postgres_clean.csv
data/processed/mongodb/mongodb_clean.csv
data/processed/json/json_clean.csv
data/comparison/comparison_report.md
```

Full details: [docs/PIPELINE_ARCHITECTURE.md](docs/PIPELINE_ARCHITECTURE.md)

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
|-- test_orchestrator.py            # 5 tests
|-- test_db_layer.py                # 10 tests
`-- test_query_layer.py             # 9 tests
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
| Database | `test_creates_database_file` | `test_db_layer.py` |
| Query | `test_returns_dataframe` | `test_query_layer.py` |
| Integration | `test_runs_successfully` | `test_orchestrator.py` |
| CLI | `test_returns_2_on_missing_file` | `test_orchestrator.py` |
| Design contract | `TestDefensiveBehavior` | `test_transform.py` |

**Total:** 61 tests passing in ~1.4 seconds.

---

## Summary table

| Decision | Guide's suggestion | Our choice | Reason |
|----------|-------------------|------------|--------|
| Structure | 3 subfolders | 11 layers + pipelines | SRP |
| Config | JSON | Python with `Final` | Type safety |
| Utilities | One file | 11 layer files | Testability |
| Database | `database/` folder | `db_layer.py` + `query_layer.py` | YAGNI |
| Multi-source | Not mentioned | `BasePipeline` + 5 subclasses | Open/Closed |
| Safety | Enforce call order | Defensive skip | Resilience |
| Tests | 1 file | 8 files | Isolation |
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
- **Multi-source architecture** with abstract base class
- **Standardization layer** for cross-source compatibility

---

## When to revisit this document

Revisit these decisions when:

1. Adding a **sixth data source** (e.g., API, Kafka, S3)
2. Adding **streaming** capabilities
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
**Version:** 3.0.0
**Last updated:** 2026-10-06
**Related files:**
- `README.md` — how to use the project
- `CHANGELOG.md` — version history
- `docs/PIPELINE_ARCHITECTURE.md` — multi-source pipeline details
- `tests/test_transform.py::TestDefensiveBehavior` — design contract
- Git history — `feat:` and `test:` commits