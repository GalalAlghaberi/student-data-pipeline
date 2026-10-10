# Silver Merge — Phase B.6 #
 طبقة دمج المصادر — من 8 مصادر إلى جدول موحّد

**Version:** v4.3.0-dev
**Baseline:** 234c0c9 (B.5 complete)
**Status:** 🔵 Planned → In Progress
**Reference:** `docs/DATA_SOURCES.md` §8 + `docs/UCI_ETL.md`
**Author:** Galal Al-Ghaberi
**Date:** 2026-10-11

---

## 1. Objective

Create a **Silver Merge layer** that unifies all 8 data sources (7 existing pipelines + UCI) into a single, well-defined dataset:

- **Input:** 8 sources with heterogeneous schemas
- **Output:** `data/silver/unified_students.parquet` (~1,136 rows × 17 cols)
- **Plus:** `data/silver/quality_report.json` (per-source coverage)

**Why now:**
- The 7 pipelines currently produce isolated outputs.
- UCI (B.5) produces its own output.
- No layer unifies them → `star_schema.py` reads only SQLite (9 students).
- The ML pipeline is capped at N=9 until merge exists.

**Non-goals:**
- Modifying any existing pipeline.
- Modifying `star_schema.py` (that is B.6.6).
- ML training (that is B.7).

---

## 2. Scope

### ✅ In Scope
| Item | Path |
|---|---|
| Merge design doc | `docs/SILVER_MERGE.md` (this file) |
| Merge implementation | `src/warehouse/silver_merge.py` |
| CLI | `scripts/run_silver_merge.py` |
| Tests | `tests/test_silver_merge.py` |
| Output (parquet) | `data/silver/unified_students.parquet` |
| Output (report) | `data/silver/quality_report.json` |

### ❌ Out of Scope
- `star_schema_v2.py` (B.6.6)
- `ml_features_large.parquet` (B.6.7)
- ML CV strategy (B.7)

---

## 3. Inputs — 8 Sources

| # | Source | Path | Schema | Est. rows | Quality |
|---|---|---|---|---|---|
| 1 | UCI | `data/processed/uci_clean.parquet` | 17 cols | 1,044 | 🟢 high |
| 2 | API | `data/processed/api/api_clean.csv` | 6 cols | ~22 | 🟡 |
| 3 | CSV | `data/processed/csv/csv_clean.csv` | 6 cols | ~8 | 🟡 |
| 4 | JSON | `data/processed/json/json_clean.csv` | 6 cols | ~3 | 🟡 |
| 5 | MongoDB | `data/processed/mongodb/mongodb_clean.csv` | 6 cols | ~10 | 🟡 |
| 6 | Postgres | `data/processed/postgres/postgres_clean.csv` | 6 cols | ~9 | 🟡 |
| 7 | Scraper | `data/processed/scraper/scraper_clean.csv` | 6 cols | ~31 | 🟡 |
| 8 | SQLite | `data/processed/sqlite/sqlite_clean.csv` | 6 cols | ~9 | 🔴 gpa=NULL |

- **Total estimated:** ~1,136 rows

### 3.1 The 6-column base schema

From `pipelines/base_pipeline.py`:

```python
STANDARD_COLUMNS = ["student_id", "name", "age", "gpa", "attendance", "city"]
```

**All 7 base sources use this exact schema** — a design win from v3.0.0.

### 3.2 Known data-quality issues

| Issue | Source | Impact |
|---|---|---|
| `gpa` and `attendance` all NULL | SQLite | 9 rows contribute no target |
| Small N | json (3), csv (8), sqlite (9) | Limited signal |
| Duplicate student_ids across base sources | probable | Will be documented |

**Decision:** keep all rows; document quality in report; **do not** silently drop.

---

## 4. Unified Schema (17 columns)

Must match `uci_clean.parquet` exactly (from `docs/UCI_ETL.md` §4.1):

| # | Column | Type | UCI | Base (6-col) |
|---|---|---|---|---|
| 1 | `record_id` | str | regenerated | generated |
| 2 | `student_id` | str | keep (`S0000`) | keep (`1001`) |
| 3 | `course` | str \| NULL | keep | NULL |
| 4 | `name` | str | keep | keep |
| 5 | `age` | Int64 | keep | keep |
| 6 | `gender` | str \| NULL | keep | NULL |
| 7 | `city` | str | keep | keep |
| 8 | `gpa` | float64 \| NULL | keep | keep (nullable) |
| 9 | `attendance_rate` | float64 \| NULL | keep | `attendance / 100` |
| 10 | `n_assessments` | Int64 \| NULL | keep (=3) | NULL |
| 11 | `score_change` | Int64 \| NULL | keep | NULL |
| 12 | `score_1` | Int64 \| NULL | keep | NULL |
| 13 | `score_2` | Int64 \| NULL | keep | NULL |
| 14 | `score_final` | Int64 \| NULL | keep | NULL |
| 15 | `school` | str \| NULL | keep | NULL |
| 16 | `address` | str \| NULL | keep | NULL |
| 17 | `source` | str | "uci" | source name |

**All columns are nullable** except `record_id`, `student_id`, `source`.

---

## 5. Transformations

### 5.1 UCI transformation

The UCI parquet is already in the target schema. Two changes:

1. **Regenerate `record_id`:** `R0000` → `R-uci-0000`
2. **Keep everything else as-is**

```python
df_uci["record_id"] = [f"R-uci-{i:04d}" for i in range(len(df_uci))]
```

### 5.2 Base source transformation

For each of the 7 base sources:

```python
def transform_base(df: pd.DataFrame, source: str) -> pd.DataFrame:
    n = len(df)
    out = pd.DataFrame({
        "record_id":       [f"R-{source}-{i:04d}" for i in range(n)],
        "student_id":      df["student_id"].astype("string"),
        "course":          pd.NA,
        "name":            df["name"].astype("string"),
        "age":             df["age"].astype("Int64"),
        "gender":          pd.NA,
        "city":            df["city"].astype("string"),
        "gpa":             df["gpa"].astype("Float64"),
        "attendance_rate": (df["attendance"] / 100.0).astype("Float64"),
        "n_assessments":   pd.NA,
        "score_change":    pd.NA,
        "score_1":         pd.NA,
        "score_2":         pd.NA,
        "score_final":     pd.NA,
        "school":          pd.NA,
        "address":         pd.NA,
        "source":          source,
    })
    return out
```

**Note on `attendance` → `attendance_rate`:**
- Base schema stores `attendance` as 0-100
- Unified schema uses `attendance_rate` as 0-1
- Conversion: `attendance / 100`

### 5.3 NaN handling

Per decision 2 (chosen A — leave NaN):
- No imputation
- No row filtering
- All columns nullable (except 3)
- Report NaN count in `quality_report.json`
- **Rationale:** honest data. B.7 will decide whether to drop NaN rows.

---

## 6. Design Decisions

### 6.1 Decision 1 — Scope: all 8 sources

**Chosen:** B (include all 7 base sources + UCI).

**Rationale:**
- Demonstrates full integration (Medallion end-to-end).
- Documents real data-quality gaps honestly.
- Preserves all sources for future enhancement.
- Base contribution (~92 rows) is small but doesn't harm.
- **Downside:** mixed data quality. Mitigation: quality report per source.

### 6.2 Decision 2 — NaN gpa: keep nullable

**Chosen:** A (leave NaN).

**Rationale:**
- Silently dropping SQLite would hide data issues.
- B.7 ML layer will filter rows with `gpa IS NOT NULL` explicitly.
- The unified schema is a "raw truth" layer, not a "clean" layer.

### 6.3 Decision 3 — record_id: source-prefixed

**Chosen:** B (`R-uci-0000`, `R-csv-0000`, ...).

**Rationale:**
- Zero collisions when new sources are added in v2.
- Traceability: `record_id` tells the source.
- UCI's existing `R0000` is transformed at merge time (`uci_clean.parquet` is not modified — Golden Rule 1).

---

## 7. Quality Report

Output: `data/silver/quality_report.json`

```json
{
  "generated_at": "2026-10-11T...",
  "total_rows": 1136,
  "total_columns": 17,
  "sources": {
    "uci":    {"rows": 1044, "gpa_filled": 1044, "attendance_filled": 1044},
    "api":    {"rows": 22,   "gpa_filled": 22,   "attendance_filled": 22},
    "csv":    {"rows": 8,    "gpa_filled": 8,    "attendance_filled": 8},
    "json":   {"rows": 3,    "gpa_filled": 3,    "attendance_filled": 3},
    "mongodb":{"rows": 10,   "gpa_filled": 10,   "attendance_filled": 10},
    "postgres":{"rows": 9,   "gpa_filled": 9,    "attendance_filled": 9},
    "scraper":{"rows": 31,   "gpa_filled": 31,   "attendance_filled": 31},
    "sqlite": {"rows": 9,    "gpa_filled": 0,    "attendance_filled": 0}
  },
  "column_coverage": {
    "record_id":       1.000,
    "student_id":      1.000,
    "course":          0.919,
    "name":            1.000,
    "age":             1.000,
    "gender":          0.919,
    "city":            1.000,
    "gpa":             0.992,
    "attendance_rate": 0.992,
    "n_assessments":   0.919,
    "score_change":    0.919,
    "score_1":         0.919,
    "score_2":         0.919,
    "score_final":     0.919,
    "school":          0.919,
    "address":         0.919,
    "source":          1.000
  }
}
```

**Note:** `gpa` coverage `0.992 = (1,136 - 9) / 1,136 ≈ 99.2%`.

---

## 8. Architecture (side-by-side)

```
┌─────────────────────────────────────────────────────────────┐
│ Silver — 8 sources                                          │
│                                                             │
│  UCI (parquet, 17 cols)                                     │
│  API, CSV, JSON, MongoDB, Postgres, Scraper, SQLite         │
│  (all CSV, 6 cols each)                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ Silver Merge (NEW)                                          │
│  src/warehouse/silver_merge.py                              │
│    ├─ load_uci()                                            │
│    ├─ load_base(source)  ×7                                 │
│    ├─ align_schema()                                        │
│    ├─ concat_all()                                          │
│    └─ write outputs                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ data/silver/                                                │
│  ├── unified_students.parquet   (~1,136 × 17)               │
│  └── quality_report.json                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
     ┌───────────────┴────────────────┐
     ↓                                ↓
┌──────────────────┐         ┌──────────────────┐
│ star_schema.py   │         │ star_schema_v2.py│
│ (frozen, 9 rows) │         │ (B.6.6, ~1136)   │
└──────────────────>         └──────────────────┘
```

---

## 9. File Plan

| # | File | Purpose |
|---|---|---|
| B.6.1 | `docs/SILVER_MERGE.md` | this file |
| B.6.2 | `src/warehouse/silver_merge.py` | merge logic (~300 lines) |
| B.6.3 | `scripts/run_silver_merge.py` | CLI (~80 lines) |
| B.6.4 | `tests/test_silver_merge.py` | ~20 tests |
| B.6.5 | `data/silver/unified_students.parquet` | output |
| B.6.6 | `data/silver/quality_report.json` | output |
| B.6.7 | `src/warehouse/star_schema_v2.py` | Gold v2 (next step) |

---

## 10. Success Criteria

| # | Criterion | Verification |
|---|---|---|
| 1 | `silver_merge.py` runs without error | CLI |
| 2 | Output parquet has ≥ 1,100 rows | file check |
| 3 | Output has exactly 17 columns | schema check |
| 4 | All `source` values ∈ {8 sources} | test |
| 5 | No `record_id` collisions | test |
| 6 | Quality report is valid JSON | test |
| 7 | 246 tests still pass | `pytest tests/ -q` |
| 8 | New tests (≥20) pass | `pytest tests/test_silver_merge.py` |
| 9 | CI remains green | GitHub Actions |
| 10 | `uci_clean.parquet` unchanged | `git diff` |

---

## 11. Risks & Mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Missing base source file | Warn + skip, continue |
| 2 | Base schema drift | Explicit column mapping |
| 3 | `student_id` collision (UCI vs base) | Document; UCI uses `S` prefix, base uses digits |
| 4 | `attendance` already 0-1 in some source | Check range; abort if max > 1.1 |
| 5 | Large parquet breaks CI memory | 1,136 rows × 17 cols ≈ 80 KB — trivial |
| 6 | JSON report with NaN | Use `default=str` in json.dumps |

---

## 12. Traceability

| Decision | Curriculum | Guide |
|---|---|---|
| Medallion architecture | Unit 10 | Ch 6 |
| Schema alignment | Unit 4 | — |
| Honest documentation | Unit 11 | Ch 12 |
| Add a layer, don't replace | — | Ch 12 |
| GroupKFold prep (B.7) | — | `DATA_SOURCES.md §7` |

---

## 13. Version History

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-11 | Initial draft after 8-source inspection |

**Last Updated:** 2026-10-11
**Status:** 🔵 Planned → In Progress
**Next Step:** B.6.2 — `src/warehouse/silver_merge.py`