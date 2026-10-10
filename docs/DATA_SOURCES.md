# Data Sources & Scale-Up Plan # مصادر البيانات وخطة التوسّع إلى $N \ge 1000$ طالب

**Version:** v4.3.0-dev  
**Baseline:** b3f6f48 (Phase B Day 1 complete)  
**Status:** 🔵 Planned → In Progress  
**Reference:** Unit 9 (Data Quality) + Guide Ch 6 (OLAP) + Guide Ch 12 (Repeatable)  
**Author:** Galal Al-Ghaberi  
**Date:** 2026-10-10  

---

## 1. Objective

Increase the ML dataset from **$N=9$** (current `ml_features.parquet`) to **$N \ge 1000$** by integrating a real-world public dataset, while:
1. Preserving the existing 7 pipelines and 9-row baseline (Golden Rule 1).
2. Introducing a **Silver Merge** layer to unify all sources.
3. Enabling ML at scale: new CV strategy, new models, production-ready.

**Educational goals:**
- Practice real ETL on a heterogeneous schema.
- Introduce **GroupKFold** (prevent student-level leakage).
- Demonstrate **Medallion architecture** end-to-end (Bronze → Silver → Gold).
- Document decisions before code (Golden Rule 4).

**Non-goals:**
- Deprecating any existing pipeline.
- Modifying `data/gold/ml_features.parquet` (frozen — 9 rows).
- Modifying `src/features/engineering.py` (frozen).

---

## 2. Current Data Sources (unchanged)

| # | Pipeline | Bronze source | Rows | Schema |
|---|---|---|---|---|
| 1 | CSV | `data/raw/students_raw.csv` | 8 | academic |
| 2 | JSON | `data/raw/students_raw.json` | 8 | academic |
| 3 | API | `data/raw/api_students.json` | 22 | academic |
| 4 | Scraper | `data/raw/web_students.html` | 31 | HTML |
| 5 | SQLite | `data/raw/university.db` | 9 | 3NF |
| 6 | PostgreSQL | `localhost:5432` | ~10 | 3NF |
| 7 | MongoDB | `localhost:27017` | ~10 docs | document |

**These remain untouched.** Their outputs continue to serve the existing `star_schema.py` (frozen at 9 students).

---

## 3. New Data Source — UCI Student Performance

### 3.1 Overview

| Property | Value |
|---|---|
| **Name** | Student Performance |
| **Source** | UCI ML Repository (dataset 320) |
| **Authors** | P. Cortez, A. M. G. Silva (2008) |
| **License** | CC0 1.0 (Public Domain) |
| **URL** | https://archive.ics.uci.edu/dataset/320 |
| **Files** | `student-mat.csv` (395 rows) + `student-por.csv` (649 rows) |
| **Total rows** | **1,044** |
| **Columns** | 33 |
| **Format** | CSV, separator = `;`, all values quoted |
| **Missing values** | 0 |
| **Shared distinct keys** | 366 (13-key matches in both files) |
| **R's merge pairs** | 382 (row-pairs, not distinct students) |
| **Unique students** | 662 (each = one 13-key) |
| **Multi-record students** | 369 ($\ge 2$ records; 366 shared + 3 within-file) |

### 3.2 Column Reference (from `student.txt`)

```text
school, sex, age, address, famsize, Pstatus,
Medu, Fedu, Mjob, Fjob, reason, guardian,
traveltime, studytime, failures,
schoolsup, famsup, paid, activities, nursery, higher, internet, romantic,
famrel, freetime, goout, Dalc, Walc, health, absences,
G1, G2, G3 (target: G3, 0-20)
```

### 3.3 Why this dataset

| Reason | Explanation |
|---|---|
| Real | 100% real student data, not synthetic |
| Proven | Cited in 100+ academic papers |
| Rich | 33 columns covering demographics, behavior, and grades |
| Target ready | G3 is a natural regression target |
| Free | CC0 license — no restrictions |

---

## 4. Unified Schema Mapping

Each UCI row will be transformed to match our project's unified schema:

| Unified field | UCI source | Transform |
|---|---|---|
| `student_id` | (generated) | `S0000` … `S0661` (one per unique student) |
| `name` | (generated) | `Student_XXXX` |
| `age` | `age` | direct |
| `gender` | `sex` | M → Male, F → Female |
| `city` | `school` + `address` | e.g., "GP-U", "GP-R", "MS-U", "MS-R" |
| `gpa` | `G3` | `G3 / 5.0` (scale 0–20 → 0–4) |
| `attendance_rate` | `absences` | `clip(1 - absences/100, 0, 1)` |
| `n_assessments` | (derived) | 3 (`G1`, `G2`, `G3`) |
| `score_change` | `G3 - G1` | direct |
| `course` | (from filename) | `"math"` or `"portuguese"` |
| `source` | (constant) | `"uci"` |

### 4.1 Extra fields kept (for future experiments)

To enable richer downstream analyses, we keep the following:
```text
school, address, famsize, Pstatus, Medu, Fedu,
Mjob, Fjob, studytime, failures, Dalc, Walc, health,
score_1 (G1), score_2 (G2), score_final (G3)
```
These are excluded from ML features (leakage audit applies) but retained for analytical exploration.

---

## 5. Design Decisions

### 5.1 Decision 1 — Dedup strategy
**Chosen:** Keep all 1,044 rows + GroupKFold by `student_id`.  
**Rationale:**
- Uses maximal data.
- Preserves the natural "same student, two courses" structure.
- Prevents a subtle form of leakage: if we randomly split, the same student's two records could land in train and test, with nearly identical features but different targets (math vs portuguese G3).
- Introduces **GroupKFold** — a transferable ML concept.  

**Implementation:**
```python
from sklearn.model_selection import GroupKFold

cv = GroupKFold(n_splits=5)
for train_idx, test_idx in cv.split(X, y, groups=df["student_id"]):
    ...
```
**Risk:** A student in train also appears in test if the 13-key merge is wrong.  
**Mitigation:** Verify unique student count = 662 in ETL tests.

### 5.2 Decision 2 — absences outliers
**Chosen:** Clip to 99th percentile of combined data.  
**Rationale:**
- Math has extreme values (max = 75 days) that would compress `attendance_rate` to $\approx 0.25$ for those students.
- Clipping at 99th percentile preserves 99% of the distribution while eliminating single-digit outliers.
- Uses combined threshold (not per-file) for consistency.  

**Implementation:**
```python
threshold = combined_df["absences"].quantile(0.99)
df["absences"] = df["absences"].clip(upper=threshold)
```
Expected threshold: $\approx 25–30$ (to be verified in ETL).

### 5.3 Decision 3 — G3 = 0 rows
**Chosen:** Keep as `gpa = 0.0` (real failure).  
**Rationale:**
- UCI documentation states G3 is the final grade (0–20).
- A 0 is a legitimate failing grade, not a missing value.
- Removing these rows would bias the model toward "successful students only".  
**Implementation:** No special handling — direct `gpa = G3 / 5.0`.

---

## 6. Student ID Assignment Strategy

### 6.1 Why is this needed?
Both `student-mat.csv` and `student-por.csv` lack a `student_id` column. The R script (`student-merge.R`) identifies duplicate students by matching 13 attributes:
```text
school, sex, age, address, famsize, Pstatus,
Medu, Fedu, Mjob, Fjob, reason, nursery, internet
```

### 6.2 Algorithm
```text
1. Concatenate both files vertically (add `course` column).
2. For each unique combination of the 13 keys, assign the same student_id.
3. Record → student_id mapping is stored for traceability.
```

### 6.3 Verification
```text
Expected unique students:       662
Expected total rows:            1,044
Expected multi-record students: 369 (≥2 records)
Expected single-record students: 293 (exactly 1 record)
R's merge reports 382 pairs (row-pairs, not distinct students).
```

> **Note on the '382' from `student-merge.R`:**  
> R's inner join on 13 keys yields `nrow(d3) = 382` PAIRS of `(math_row, por_row)`. When a student has multiple rows per file (within-file 13-key collision), R generates multiple pairs per student. Our algorithm assigns one `student_id` per unique 13-key, so 369 DISTINCT students have $\ge 2$ records.  
> These numbers are asserted in `tests/test_uci_pipeline.py`.

---

## 7. GroupKFold Strategy

### 7.1 Why GroupKFold?
Standard KFold randomly assigns rows to folds. With duplicate students:
```text
Student S0042 → row_1 (math, absences=2, G3=10)
              → row_2 (por,  absences=2, G3=14)

Random split might do:
  row_1 → train
  row_2 → test

Result: near-identical X, different y → apparent overfitting.
```
GroupKFold guarantees:
```text
All rows of student S0042 → same fold (either all train or all test).
```

### 7.2 Configuration
| Parameter | Value | Reason |
|---|---|---|
| `n_splits` | 5 | Standard for $N \approx 1000$ |
| `groups` | `df["student_id"]` | Enforce student isolation |
| `shuffle` | N/A | GroupKFold has no shuffle |

### 7.3 Comparison with Day 1
| Aspect | Day 1 ($N=9$) | Scale-Up ($N=1044$) |
|---|---|---|
| Primary CV | LeaveOneOut | GroupKFold(5) |
| Secondary CV | KFold(3) | KFold(5) on aggregated 662 |
| Reason | $N$ too small for folds | $N$ large enough for 5-fold |

---

## 8. Silver Merge Architecture

### 8.1 Motivation
Currently, `star_schema.py` reads only from `university.db` (9 students). The 7 pipelines produce intermediate outputs but are never merged. The Silver Merge layer fixes this by:
- Reading from all pipelines (7 + UCI).
- Aligning schemas.
- Deduplicating.
- Producing a single unified dataset.

### 8.2 Architecture (side-by-side, honoring Golden Rule 1)
```text
Bronze Layer
  ├── 7 existing sources (data/raw/)
  └── UCI: data/raw/uci/*.csv                         ← 🆕
                ↓
Silver Layer
  ├── pipelines/*_pipeline.py  (7 existing — untouched)
  └── pipelines/uci_pipeline.py                       ← 🆕
                ↓
Silver Merge (NEW)
  └── src/warehouse/silver_merge.py                   ← 🆕
      ├── Reads: data/processed/*.parquet (unified schema)
      ├── Aligns schemas
      ├── Deduplicates by (name, age, city)
      └── Writes: data/silver/unified_students.parquet
                ↓
Gold Layer (side-by-side)
  ├── star_schema.py    → 9 students  (FROZEN)
  └── star_schema_v2.py → 1000+ students              ← 🆕
                ↓
Feature Store
  ├── ml_features.parquet        (9 rows — FROZEN)
  └── ml_features_large.parquet  (1000+ rows)     ← 🆕
                ↓
ML Layer (side-by-side)
  ├── src/ml/*  (Day 1 — untouched)
  └── src/ml/*_v2.py  (GroupKFold + new models)       ← 🆕
```

### 8.3 Why side-by-side?
| Approach | Risk | Verdict |
|---|---|---|
| Refactor `star_schema.py` | Breaks 26 warehouse tests + 22 feature tests | ❌ |
| Add `star_schema_v2.py` | Zero breakage; enables A/B comparison | ✅ |

*Golden Rule 1 — add a layer, do not replace.*

---

## 9. Phase Plan

### 9.1 Phase B.5 — UCI Integration (2–3 days)
**Goal:** Load UCI data and produce unified-schema parquet.

| # | File | Deliverable |
|---|---|---|
| B.5.1 | `docs/DATA_SOURCES.md` | this file |
| B.5.2 | `scripts/inspect_uci_data.py` | ✅ done |
| B.5.3 | `pipelines/uci_pipeline.py` | ETL: CSV → unified schema |
| B.5.4 | `data/processed/uci_clean.parquet` | 1,044 rows × 11 cols |
| B.5.5 | `tests/test_uci_pipeline.py` | ~15 tests |
| B.5.6 | `docs/UCI_ETL.md` | ETL documentation |

### 9.2 Phase B.6 — Silver Merge (4–5 days)
**Goal:** Unify all sources into `data/silver/unified_students.parquet`.

| # | File | Deliverable |
|---|---|---|
| B.6.1 | `docs/SILVER_MERGE.md` | design doc |
| B.6.2 | `src/warehouse/silver_merge.py` | merge logic |
| B.6.3 | `scripts/run_silver_merge.py` | CLI |
| B.6.4 | `data/silver/unified_students.parquet` | final dataset |
| B.6.5 | `tests/test_silver_merge.py` | ~15 tests |
| B.6.6 | `src/warehouse/star_schema_v2.py` | Gold v2 |
| B.6.7 | `data/gold/ml_features_large.parquet` | ML input |

### 9.3 Phase B.7 — ML Scale-Up (3–4 days)
**Goal:** Run ML on $N \ge 1000$ with proper CV.

| # | File | Deliverable |
|---|---|---|
| B.7.1 | `docs/ML_EXPERIMENTS_SCALE.md` | updated experiments doc |
| B.7.2 | `src/ml/split_v2.py` | GroupKFold + KFold(5) |
| B.7.3 | `src/ml/trainer_v2.py` | RandomForest, GradientBoosting |
| B.7.4 | `src/ml/pipeline_v2.py` | orchestrator (v2) |
| B.7.5 | `scripts/run_ml_pipeline_v2.py` | CLI |
| B.7.6 | `tests/test_ml_v2.py` | ~20 tests |
| B.7.7 | `data/gold/model_metrics_v2.csv` | results |

---

## 10. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | 13-key merge falsely merges 2 distinct students | Low | Medium | Assert unique count = 662 |
| 2 | Schema mismatch between UCI and existing | Medium | High | Explicit mapping table (§4) |
| 3 | GroupKFold splits fail silently | Low | High | Test that no `student_id` appears in both train and test |
| 4 | `absences` clip destroys signal | Low | Medium | Verify 99th percentile range in tests |
| 5 | `G3=0` biases model | Medium | Medium | Document in findings; report count |
| 6 | `ml_features.parquet` accidentally overwritten | Low | Critical | Use new filename `_large.parquet` |
| 7 | Silver Merge reads broken pipelines | Medium | Medium | Test each source independently first |

---

## 11. Success Criteria

Phase B.5 + B.6 + B.7 complete when:

| # | Criterion | Verification |
|---|---|---|
| 1 | `docs/DATA_SOURCES.md` exists | this file |
| 2 | `pipelines/uci_pipeline.py` exists | `ls pipelines/` |
| 3 | `data/processed/uci_clean.parquet` has 1,044 rows | `python -c "import pandas; print(len(pandas.read_parquet(...)))"` |
| 4 | `silver_merge.py` produces unified dataset | manual + test |
| 5 | Unique students = 662 | test assertion |
| 6 | `ml_features_large.parquet` has 1000+ rows | file check |
| 7 | GroupKFold works: no `student_id` in both folds | test |
| 8 | All existing 221 tests pass | `pytest tests/ -q` |
| 9 | New tests pass ($\ge 50$) | `pytest tests/test_uci_pipeline.py tests/test_silver_merge.py tests/test_ml_v2.py` |
| 10 | CI remains green | GitHub Actions |
| 11 | `ml_features.parquet` unchanged (9 rows) | `git diff` |
| 12 | `star_schema.py` unchanged | `git diff` |

---

## 12. Timeline

| Phase | Duration | Cumulative |
|---|---|---|
| B.5 | 2–3 days | 2–3 days |
| B.6 | 4–5 days | 6–8 days |
| B.7 | 3–4 days | 9–12 days |

---

## 13. Decisions Log

| Date | Decision | Choice | Rationale |
|---|---|---|---|
| 2026-10-10 | Dataset | UCI Student Performance | Real, free, proven |
| 2026-10-10 | Dedup | A: 1,044 rows + GroupKFold | Max data + leakage prevention |
| 2026-10-10 | `absences` | B: clip @ 99th percentile | Preserve distribution |
| 2026-10-10 | `G3=0` | A: keep as `gpa=0` | Real failure, not missing |
| 2026-10-10 | Architecture | Side-by-side | Golden Rule 1 |

---

## 14. References

| Ref | Source |
|---|---|
| UCI dataset | https://archive.ics.uci.edu/dataset/320 |
| Cortez & Silva 2008 | "Using Data Mining to Predict Secondary School Student Performance" |
| `student.txt` | `data/raw/uci/student.txt` |
| `student-merge.R` | `data/raw/uci/student-merge.R` |
| Guide Ch 6 | OLAP + Medallion |
| Guide Ch 12 | Repeatable / Resilient / Scalable |
| Unit 9 | Data Quality |
| `docs/ML_EXPERIMENTS.md` | Day 1 baseline |

---

## 15. Version History

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-10 | Initial draft after UCI inspection |

---

**Last Updated:** 2026-10-10  
**Status:** 🔵 Planned → In Progress  
**Next Step:** B.5.3 — `pipelines/uci_pipeline.py`