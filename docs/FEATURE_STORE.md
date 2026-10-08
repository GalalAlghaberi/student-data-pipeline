# Feature Store — Phase A

**Version:** v4.0.0-dev
**Baseline:** b8a1a73
**Status:** Implemented

---

## 1. Objective

Build an ML-ready Feature Store on top of the Gold (Star Schema) layer,
with strict **Data Leakage Prevention** (Unit 9, pp. 76-77).

**Golden Rules:**
1. Add a layer; do not replace existing layers.
2. All new code in `src/features/` — no changes to `src/warehouse/`.
3. All 140 v3.0.0 tests remain green.
4. Documentation before code.

---

## 2. Inputs (Read-Only)

| Table | Path | Grain | Rows |
|---|---|---|---|
| dim_students | `data/gold/dim_students.parquet` | 1 student | 8 |
| dim_courses | `data/gold/dim_courses.parquet` | 1 course | 5 |
| dim_instructors | `data/gold/dim_instructors.parquet` | 1 instructor | 4 |
| dim_time | `data/gold/dim_time.parquet` | 1 date | 4 |
| fact_student_performance | `data/gold/fact_student_performance.parquet` | 1 assessment | 26 |
| fact_enrollment | `data/gold/fact_enrollment.parquet` | 1 enrollment | 13 |

**Rebuild:** `python -m src.warehouse.star_schema`

---

## 3. Outputs

| File | Grain | Purpose |
|---|---|---|
| `ml_features.parquet` | 1 student | Model training input |
| `train_test_split.parquet` | 1 student | Split assignment |
| `feature_metadata.json` | 1 feature | Catalog + train stats |

**Note:** `data/gold/` is gitignored (fully regenerable).

---

## 4. Feature Catalog

| Feature | Formula | Source | Leakage Risk |
|---|---|---|---|
| `attendance_rate` | `attendance / 100` | Unit 6, p. 37 | none |
| `academic_risk_score` | `(4 - gpa) + ((100 - attendance) / 25)` | Unit 6, p. 51 | none |
| `score_change` | `score - LAG(score) OVER (PARTITION BY student_id, course_id ORDER BY assessment_id)` | Unit 3, pp. 36-38 | none |
| `city_rank` | `RANK() OVER (PARTITION BY city ORDER BY avg_score DESC)` from TRAIN only | Unit 3, p. 33 | high |
| `city_score_gap` | `avg_score - median(city avg_score in TRAIN)` | Design | low |
| `performance_level` | `CASE WHEN avg_score >= 90 THEN 'Excellent' ...` | Unit 3, p. 19 | none |

### Performance Levels
- `>= 90` → Excellent
- `>= 80` → Very Good
- `>= 70` → Good
- `>= 60` → Pass
- `< 60` → Weak

---

## 5. Data Leakage Prevention

### Protocol (Unit 9, pp. 76-77)

1. Load Gold layer
2. Build base features (row-wise, leak-free)
3. **Split TRAIN/TEST first**
4. Compute statistics from **TRAIN ONLY**:
   - `gpa_median`
   - `attendance_median`
   - `avg_score_median`
5. Apply TRAIN statistics to both TRAIN and TEST
6. Compute `city_rank` and `city_score_gap` from **TRAIN peers only**
7. Validate
8. Save

### Forbidden

| Forbidden | Correct |
|---|---|
| `df["gpa"].median()` on full data | `train["gpa"].median()` |
| `df.groupby("city").mean()` before split | `train.groupby("city").mean()` |

### Reference

> "If we use `df['gpa'].median()` to calculate a missing-value replacement
> using the entire Dataset before splitting the data into Training and Test sets,
> information from the Test set may enter the training preprocessing process."
> — Unit 9, p. 76

---

## 6. Architecture

src/
├── warehouse/ <- Phase 2 (untouched)
└── features/ <- Phase A (new)
├── init.py
└── engineering.py

data/gold/
├── dim_.parquet <- Phase 2
├── fact_.parquet <- Phase 2
├── ml_features.parquet <- Phase A (new)
├── train_test_split.parquet <- Phase A (new)
└── feature_metadata.json <- Phase A (new)

tests/
└── test_features.py <- Phase A (new, 22 tests)

text

---

## 7. Public API

```python
class FeatureEngineer:
    def __init__(self, gold_dir, test_size=0.2, random_state=42): ...
    def load_gold(self): ...
    def build_base_features(self): ...
    def split_train_test(self): ...
    def compute_train_statistics(self): ...      # TRAIN ONLY
    def apply_statistics(self): ...              # TRAIN + TEST
    def compute_city_rank(self): ...             # TRAIN peers only
    def validate(self): ...
    def save(self): ...
    def run(self): ...
Guarantees
Grain: 1 row per student

student_id unique

No NaN in critical features

attendance_rate in [0, 1]

split in {train, test}

Idempotent (fixed random_state=42)
---

## 8. Tests 

tests/test_features.py — 22 tests:

Category	Tests
Loading	2
Base features	6
Split	3
Leakage prevention	3
City features	2
Validation	2
Persistence	2
Idempotency	1
Catalog	2
Result: 140 -> 162 passed.

## 9. Idempotency
Re-running python -m src.features.engineering:

Overwrites ml_features.parquet (no append)

Same random_state=42 -> identical split

Deterministic ordering

## 10. Usage

bash
# Rebuild features
python -m src.features.engineering

# Run tests
python -m pytest tests/test_features.py -v
## 11. Traceability

Decision	Curriculum	Guide
LAG for temporal	Unit 3, pp. 36-38	—
RANK PARTITION BY	Unit 3, p. 33	—
CASE for classification	Unit 3, p. 19	—
Leakage prevention	Unit 9, pp. 76-77	—
Parquet format	—	Ch 4, pp. 11-12
| Explicit grain | Unit 4, p. 58 | Ch 8 |
| Idempotency | Unit 10, p. 17 | — |
| Add layer, don't replace | — | Ch 12 |

---

**Last Updated:** 2026-10-08
**Status:** Implemented (Phase A)