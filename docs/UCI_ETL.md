# UCI ETL — Phase B.5

# خط أنابيب تحويل بيانات UCI إلى المخطط الموحّد

**Version:** v4.3.0-dev
**Baseline:** 4fc6378 (UCI sources + inspect script committed)
**Status:** 🔵 Planned → In Progress
**Reference:** `docs/DATA_SOURCES.md` §4-5
**Author:** Galal Al-Ghaberi
**Date:** 2026-10-10

## 1. Objective

Transform the raw UCI Student Performance CSVs (1,044 rows × 33 cols
across two files) into a **single unified-schema parquet** that matches
the rest of the project, and that feeds the future Silver Merge layer.

**Input:**

* `data/raw/uci/student-mat.csv` (395 rows, math)

* `data/raw/uci/student-por.csv` (649 rows, portuguese)

**Output:**

* `data/processed/uci_clean.parquet` (1,044 rows × 17 cols)

**Goals:**

1. Preserve both files as separate records (`course` column).

2. Assign the **same `student_id`** to students appearing in both files.

3. Apply the 3 design decisions (dedup, absences clip, G3=0).

4. Document the transformation, not just execute it.

**Non-goals:**

* Modifying the 7 existing pipelines.

* Producing the final Silver Merge (that is B.6).

* Any ML training (that is B.7).

## 2. Input Files

### 2.1 Files at a glance

| File | Rows | Separator | Quote | Encoding | 
| ----- | ----- | ----- | ----- | ----- | 
| `student-mat.csv` | 395 | `;` | `"` | UTF-8 | 
| `student-por.csv` | 649 | `;` | `"` | UTF-8 | 

### 2.2 Column contract (33 columns)

```
school, sex, age, address, famsize, Pstatus,
Medu, Fedu, Mjob, Fjob, reason, guardian,
traveltime, studytime, failures,
schoolsup, famsup, paid, activities, nursery, higher,
internet, romantic,
famrel, freetime, goout, Dalc, Walc, health,
absences,
G1, G2, G3

```

All values are quoted strings in the raw CSV, even numeric ones.
Loading must use `sep=";"` and `dtype=str` initially, then cast
numeric columns explicitly.

## 3. Student ID Assignment Algorithm

### 3.1 Why needed

UCI files have **no `student_id`** column. The 366 students shared
by both files (by 13-key match) are identified by matching 13 attributes
(per `student-merge.R`).

### 3.2 The 13 merge keys (verbatim from R script)

```
MERGE_KEYS = [
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "nursery", "internet",
]

```

### 3.3 Algorithm

1. Load math: add course = "math"

2. Load por:  add course = "portuguese"

3. Concat vertically → 1,044 rows

4. Compute per-row merge_key = tuple(row\[k\] for k in MERGE_KEYS)

5. Deduplicate merge_keys → assign student_id = "S0000", "S0001", ...

6. Map every row to its student_id via merge_key

7. Verify: unique student_id count == 662

On the '382' from `student-merge.R`:

R's script reports `nrow(d3) = 382`. This counts `(math_row, por_row)`

PAIRS, not distinct students. When a student has multiple rows in

one file (within-file 13-key collision), R generates multiple pairs.

Our algorithm assigns one `student_id` per unique 13-key, so the

number of DISTINCT students with $\ge 2$ records is 369 (verified in

`data/processed/uci_clean.parquet`). The 3-student gap between 366

shared distinct keys and 369 multi-record students comes from

students with within-file collisions only (no cross-file match).

### 3.4 Two identifiers, two purposes

| Column | Purpose | Uniqueness | 
| ----- | ----- | ----- | 
| `record_id` | Row identity (1 per record) | 1,044 unique values | 
| `student_id` | Student identity (across files) | 662 unique values | 

**Example:**

| record_id | student_id | course | G3 | 
| ----- | ----- | ----- | ----- | 
| R0000 | S0000 | math | 6 | 
| R0001 | S0001 | math | 6 | 
| ... | ... | ... | ... | 
| R0500 | S0042 | portuguese | 14 | 
| R0800 | S0042 | portuguese | 11 | 

In this example, `student_id S0042` has 2 records: one with `math`, one with `portuguese`.
Note: some students have MORE than 2 records due to within-file 13-key collisions (e.g., two identical rows in `student-mat.csv`). The data contains 369 multi-record students; 293 appear exactly once.

## 4. Column Transformation Mapping

### 4.1 Output schema (17 columns)

| \# | Column | Type | Source | Transform | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | `record_id` | str | (generated) | R0000 … R1043 | 
| 2 | `student_id` | str | (generated) | S0000 … S0661 | 
| 3 | `course` | category | (from file) | "math" / "portuguese" | 
| 4 | `name` | str | (generated) | Student_S0000 | 
| 5 | `age` | int64 | `age` | direct | 
| 6 | `gender` | str | `sex` | M → Male, F → Female | 
| 7 | `city` | str | `school` + `address` | "GP-U", "GP-R", "MS-U", "MS-R" | 
| 8 | `gpa` | float64 | `G3` | `G3 / 5.0` | 
| 9 | `attendance_rate` | float64 | `absences` | `clip(1 - absences/100, 0, 1)` | 
| 10 | `n_assessments` | int64 | (derived) | 3 (G1, G2, G3) | 
| 11 | `score_change` | int64 | `G3 - G1` | direct | 
| 12 | `score_1` | int64 | `G1` | direct (kept for reference) | 
| 13 | `score_2` | int64 | `G2` | direct (kept for reference) | 
| 14 | `score_final` | int64 | `G3` | direct (kept for reference) | 
| 15 | `school` | str | `school` | direct (analytical) | 
| 16 | `address` | str | `address` | direct (analytical) | 
| 17 | `source` | str | (constant) | "uci" | 

### 4.2 Why 17 columns and not 11?

The `DATA_SOURCES.md` §4 lists 11 unified fields. We keep 3 extra score columns (`score_1`, `score_2`, `score_final`) and 2 extra analytical columns (`school`, `address`) to enable:

* Day 2 experiments: does G1 predict G3 better than the other features?

* Silver Merge dedup: matching against existing sources needs more keys.

* Traceability: verify `gpa == score_final / 5` after loading.

The ML layer will filter these down to the 6 safe features.

## 5. Design Decisions (Implementation)

### 5.1 Dedup — keep 1,044 rows

Per `DATA_SOURCES.md` §5.1: GroupKFold by `student_id`.

* We do not collapse the 366 shared students here (369 including within-file collisions).

* The ETL preserves both records; the ML splitter enforces isolation.

### 5.2 Absences — clip to 99th percentile

Computed on combined data (1,044 rows), not per-file.

```
threshold = df["absences"].quantile(0.99)
df["absences"] = df["absences"].clip(upper=threshold)

```

* Expected threshold: $\approx 25–30$.

* Verify: after clipping, `absences.max() == threshold`.

### 5.3 G3 = 0 — keep as `gpa = 0.0`

* No filtering, no imputation.

* Count of `G3 == 0` rows is logged for transparency.

* Expected: $\approx 40$ rows ($\approx 4\%$ of 1,044).

## 6. Verification Checks (post-ETL)

The pipeline runs these assertions automatically:

| \# | Check | Expected | 
| ----- | ----- | ----- | 
| 1 | Row count | 1,044 | 
| 2 | Column count | 17 | 
| 3 | Unique `student_id` | 662 | 
| 4 | Unique `record_id` | 1,044 | 
| 4b | Multi-record students (`student_id` count $\ge 2$) | 369 | 
| 4c | Single-record students (`student_id` count $== 1$) | 293 | 
| 5 | `course` values | `{math, portuguese}` | 
| 6 | `gender` values | `{Male, Female}` | 
| 7 | `city` values | `{GP-U, GP-R, MS-U, MS-R}` | 
| 8 | `gpa` range | $[0.0, 4.0]$ | 
| 9 | `attendance_rate` range | $[0.0, 1.0]$ | 
| 10 | `absences.max()` | == clip threshold | 
| 11 | `score_change == score_final - score_1` | all rows | 
| 12 | No missing values | 0 total | 

Any failure raises `AssertionError` with diagnostic context.

## 7. CLI

```
python -m pipelines.uci_pipeline
python -m pipelines.uci_pipeline --raw-dir data/raw/uci
python -m pipelines.uci_pipeline --output data/processed/uci_clean.parquet
python -m pipelines.uci_pipeline --log-level DEBUG

```

Default behavior:

* Reads from `data/raw/uci/`

* Writes to `data/processed/uci_clean.parquet`

* Runs all 12 verification checks

* Prints a summary

## 8. Testing Strategy

`tests/test_uci_pipeline.py` ($\approx 15$ tests):

| \# | Test | What it verifies | 
| ----- | ----- | ----- | 
| 1 | `test_load_mat_shape` | $(395, 33)$ | 
| 2 | `test_load_por_shape` | $(649, 33)$ | 
| 3 | `test_load_uses_semicolon` | Detects wrong separator | 
| 4 | `test_concat_total_rows` | 1,044 | 
| 5 | `test_unique_students_662` | Student ID algorithm | 
| 6 | `test_unique_records_1044` | Record ID algorithm | 
| 7 | `test_course_values` | `{math, portuguese}` | 
| 8 | `test_gender_mapping` | M→Male, F→Female | 
| 9 | `test_city_4_values` | GP-U, GP-R, MS-U, MS-R | 
| 10 | `test_gpa_range` | $[0, 4]$ | 
| 11 | `test_attendance_range` | $[0, 1]$ | 
| 12 | `test_absences_clipped` | max == threshold | 
| 13 | `test_score_change_formula` | `score_final - score_1` | 
| 14 | `test_no_missing_values` | `isnull().sum() == 0` | 
| 15 | `test_output_parquet_written` | File exists + readable | 

Marker: all tests run in CI (no network/db markers needed).

## 9. Risks & Mitigations (specific to ETL)

| \# | Risk | Likelihood | Impact | Mitigation | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | 13-key merge over-merges | Low | High | Assert 662 unique students | 
| 2 | 13-key merge under-merges | Low | Medium | Compare to R script result (382) | 
| 3 | 99th percentile too aggressive | Low | Medium | Log threshold + row count affected | 
| 4 | Dtype mismatch in parquet | Medium | Low | Explicit `.astype()` before write | 
| 5 | `student_id` collides with existing sources | Low | Low | Prefix `S` distinguishes UCI from others | 

## 10. Output Contract

* **File:** `data/processed/uci_clean.parquet`

* **Rows:** 1,044

* **Columns:** 17 (see §4.1)

* **File size:** $\approx 50-80$ KB

Downstream consumers:

* `src/warehouse/silver_merge.py` (B.6) — will read this file.

* `docs/SILVER_MERGE.md` (B.6) — documents the merge.

* Any future analysis notebook.

Do NOT modify this file manually — regenerate via:

```
python -m pipelines.uci_pipeline

```

## 11. Traceability

| Decision | Curriculum | Guide | Doc reference | 
| ----- | ----- | ----- | ----- | 
| Leakage prevention | Unit 9 | Ch 9 | §5.1 | 
| GroupKFold rationale | Applied ML Day 2 | — | `DATA_SOURCES.md` §7 | 
| absences clipping | Unit 9 | — | §5.2 | 
| G3=0 handling | — | Ch 12 | §5.3 | 
| Documentation first | Unit 11 | Ch 12 | this file | 
| Add a layer, not replace | — | Ch 12 | `DATA_SOURCES.md` §8 | 

## 12. Version History

| Version | Date | Change | 
| ----- | ----- | ----- | 
| v0.1 | 2026-10-10 | Initial draft (B.5.6) | 

**Last Updated:** 2026-10-10
**Status:** 🔵 Planned → In Progress