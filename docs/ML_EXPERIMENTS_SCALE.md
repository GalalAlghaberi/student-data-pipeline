# ML Experiments — Phase B.7 (Scale-Up) / تجارب تعلّم الآلة — المرحلة B.7 (التوسّع إلى $N=1044$)

**Version:** `v4.3.0-dev`

**Baseline:** `a9c4e6b` (Phase B.6 complete)

**Status:** ✅ Complete

**Reference:** `docs/ML_EXPERIMENTS.md` (Day 1, $N=9$) + `docs/SILVER_MERGE.md`

**Author:** Galal Al-Ghaberi

**Date:** 2026-10-11

## 1. Objective

Scale the ML layer from $N=9$ (Day 1, synthetic features) to $N=1044$ (Phase B.5 UCI rows) using the Phase B.6 Silver dataset (`data/silver/unified_students.parquet`), while preserving every existing artifact (`src/ml/*`, `ml_features.parquet`, 269 tests).

**Primary goals:**

1. Replace **LeaveOneOut** (mandatory at $N=9$) with **GroupKFold(5)** to enforce student-level isolation.

2. Introduce **tree-based models** (RandomForest, GradientBoosting) — impossible at $N=9$.

3. Report **honest feature importance** at scale.

4. Compare **v1 (**$N=9$**)** vs **v2 (**$N=1044$**)** head-to-head.

**Educational goals:**

* Practice **leakage re-audit** on a wider schema (17 columns).

* Introduce **group-aware CV** — a transferable concept.

* Demonstrate **multicollinearity detection** (city vs school+address).

* Demonstrate **ablation** (FS-A vs FS-B).

**Non-goals:**

* Modifying `src/ml/*` (v1) — Golden Rule 1.

* Modifying `ml_features.parquet` (9 rows — FROZEN).

* Hyperparameter tuning beyond a documented baseline (deferred to B.8).

* Deep learning.

## 2. Dataset

| Property | Value | 
| ----- | ----- | 
| Source | `data/silver/unified_students.parquet` (Phase B.6) | 
| Total rows | 1,121 (all 8 sources) | 
| **Rows used** | **1,044** (UCI-only) | 
| Rows excluded | 77 (base sources — see §2.1) | 
| Columns | 17 | 
| Target | `gpa` (float, $[0, 4]$) | 
| Missing in used rows | 0 (UCI has no NaN) | 
| Unique students (`student_id`) | **662** | 
| Multi-record students | 369 ($\ge 2$ rows: math + por) | 

### 2.1 Why UCI-only ($N=1044$)?

The Silver dataset contains 1,121 rows from 8 sources. The 77 non-UCI rows are distributed as follows (from `silver_merge.py` actual output):

| Source | Rows | gpa filled | 
| ----- | ----- | ----- | 
| api | 30 | 0 | 
| csv | 8 | 8 | 
| json | 3 | 3 | 
| mongodb | 10 | 10 | 
| postgres | 8 | 0 | 
| scraper | 10 | 10 | 
| sqlite | 8 | 0 | 
| **Total (non-UCI)** | **77** | **31** | 

These 77 rows suffer from severe feature sparsity:

| Issue | Sources affected | 
| ----- | ----- | 
| `gender`, `course`, `school`, `address` = NaN | all 7 base sources | 
| `score_1`, `score_2`, `score_final` = NaN | all 7 base sources | 
| `n_assessments` = NaN | all 7 base sources | 
| `gpa` = NaN | api, postgres, sqlite (46 rows) | 

Including them would require 8+ imputation strategies, each with its own bias. The Silver layer is honest about this (see `quality_report.json`) — but the ML layer must decide, and the honest decision is **UCI-only**.

**Decision:** filter `df["source"] == "uci"` at load time. Documented as a design choice, not a silent drop.

### 2.2 Filtering pipeline

```
df_silver = pd.read_parquet("data/silver/unified_students.parquet")
df_uci    = df_silver[df_silver["source"] == "uci"].copy()
# Sanity: len(df_uci) == 1044; df_uci["gpa"].notna().all() == True

```

## 3. Leakage Re-Audit (CRITICAL — Unit 9, pp. 76-77)

The Silver schema exposes 17 columns vs Day 1's 15. A full re-audit is mandatory before any feature is selected.

### 3.1 Column-by-column verdict

| \# | Column | Formula / Source | Verdict | 
| ----- | ----- | ----- | ----- | 
| 1 | `record_id` | synthetic ID | ⛔ excluded (identifier) | 
| 2 | `student_id` | synthetic ID | ⛔ excluded (CV group only) | 
| 3 | `course` | "math" / "portuguese" | ✅ safe (categorical) | 
| 4 | `name` | "Student_S0042" | ⛔ excluded (text, no signal) | 
| 5 | `age` | direct | ✅ safe | 
| 6 | `gender` | M→Male, F→Female | ✅ safe | 
| 7 | `city` | school + address merged | ✅ safe (see §3.3) | 
| 8 | `gpa` | TARGET | 🎯 target | 
| 9 | `attendance_rate` | clip(1 - absences/100, 0, 1) | ✅ safe | 
| 10 | `n_assessments` | constant = 3 | ⚠️ zero variance (excluded) | 
| 11 | `score_change` | score_final - score_1 | ❌ LEAKY | 
| 12 | `score_1` | G1 (first period) | 🟡 temporal signal (see §4) | 
| 13 | `score_2` | G2 (second period) | 🟡 temporal signal (see §4) | 
| 14 | `score_final` | G3 = gpa $\times 5$ | ❌ LEAKY | 
| 15 | `school` | "GP" / "MS" | 🟡 collinear with city (see §3.3) | 
| 16 | `address` | "U" / "R" | 🟡 collinear with city (see §3.3) | 
| 17 | `source` | constant = "uci" | ⚠️ zero variance (excluded) | 

### 3.2 Algebraic leakage proofs

**`score_final` (row 14) — the worst offender:**

$$
\text{In UCI\_ETL.md } \S 4.1: \quad gpa = \frac{G3}{5.0}, \quad \text{score\_final} = G3 \implies gpa = \frac{\text{score\_final}}{5.0}
$$

Using `score_final` to predict `gpa` is predicting $5 \times gpa$ from $gpa$. This is the exact analogue of Day 1's `avg_score` leakage (`ML_EXPERIMENTS.md` §3.1). $R^2$ would be exactly 1.0 with a trivial model.

**`score_change` (row 11) — indirect leak:**

$$
\text{score\_change} = \text{score\_final} - \text{score\_1} = 5 \times gpa - \text{score\_1}
$$

Predicting `gpa` from `score_change` is predicting `gpa` from $5 \times gpa - \text{score\_1}$. Still a direct algebraic dependency on the target.

**Verdict:** both `score_final` and `score_change` are forbidden in every feature set. A regression test (`test_no_leaky_features_v2`) will assert this.

### 3.3 Multicollinearity: $\text{city} \supset \text{school} \cup \text{address}$

The UCI ETL defines:

$$
\text{city} = \text{"\{school\}-\{address\}"} \quad (\text{e.g., "GP-U", "GP-R", "MS-U", "MS-R"})
$$

Therefore:

* $\text{school} \in \{\text{GP, MS}\} \to 2$ levels

* $\text{address} \in \{\text{U, R}\} \to 2$ levels

* $\text{school} \times \text{address} \to 4$ combinations = city's 4 levels

Including all three would give the encoder:

* `city` (OneHot $\to 4$ dummies)

* `school` (OneHot $\to 2$ dummies, perfectly determined by city)

* `address` (OneHot $\to 2$ dummies, perfectly determined by city)

This creates a singular design matrix — `LinearRegression` would silently pick an arbitrary solution among infinitely many, and feature importances would be meaningless.

**Decision:** use `city` only in feature sets. Keep `school` and `address` as preserved columns (not dropped from the parquet) for future analytical use, but exclude them from every FS.

### 3.4 `source` and `n_assessments`: zero variance

Both columns are constant over UCI-only rows:

* `source == "uci"` for $1,044 / 1,044$ rows.

* `n_assessments == 3` for $1,044 / 1,044$ rows (math + por each have G1, G2, G3).

Zero-variance columns:

* Are dropped by sklearn's `VarianceThreshold(0.0)` silently.

* Contribute 0 to every model.

* Pollute feature-importance tables with $0.0000$.

**Decision:** exclude both from every FS. `source` remains in the parquet (needed for filtering); `n_assessments` is kept for traceability but not used.

### 3.5 Forbidden patterns (documented)

```
# ❌ WRONG — score_final leaks the target
X = df[["score_final", "age"]]
y = df["gpa"]  # R² will be 1.0, model is useless

# ❌ WRONG — score_change derives from score_final
X = df[["score_change", "attendance_rate"]]
y = df["gpa"]

# ❌ WRONG — school+address+city are collinear
X = df[["city", "school", "address"]]

# ✅ CORRECT — FS-A (demographic-only baseline)
X = df[["attendance_rate", "age", "gender", "city", "course"]]
y = df["gpa"]

# ✅ CORRECT — FS-B (temporal signal augmentation)
X = df[["attendance_rate", "age", "gender", "city", "course", "score_1", "score_2"]]
y = df["gpa"]

```

## 4. Feature Sets (FS-A, FS-B)

Two feature sets are evaluated in parallel. This is a deliberate ablation study — not indecision.

### 4.1 FS-A — Demographic-only baseline

**Hypothesis:** How much can be predicted from non-academic context?

| Feature | Type | Range / Values | Source | 
| ----- | ----- | ----- | ----- | 
| `attendance_rate` | numeric | $[0.744, 1.000]$ | absences | 
| `age` | numeric | $[15, 22]$ | direct | 
| `gender` | categorical | $\{\text{Male, Female}\}$ | sex | 
| `city` | categorical | $\{\text{GP-U, GP-R, MS-U, MS-R}\}$ | school+address | 
| `course` | categorical | $\{\text{math, portuguese}\}$ | filename | 

Total: 3 numeric + 3 categorical $\to$ OneHot $\to$ 7 encoded columns.

**Why this set:**

* All features are context; none are grades.

* If $R^2$ is high, demographics alone "explain" GPA — a controversial but often-observed result in education data.

* If $R^2$ is near zero, GPA genuinely requires academic history.

### 4.2 FS-B — Temporal signal augmentation

FS-A + the two prior-period grades:

| Feature | Type | Range | Note | 
| ----- | ----- | ----- | ----- | 
| `score_1` | numeric | $[0, 20]$ | G1 — first period | 
| `score_2` | numeric | $[0, 20]$ | G2 — second period | 

Total: 5 numeric + 3 categorical $\to$ OneHot $\to$ 9 encoded columns.

**Why is this legal?**

* `score_1` and `score_2` are prior measurements, not the target.

* They are conceptually "grades before the final exam" — a real predictor a school would legitimately have when trying to forecast final GPA.

* They are NOT algebraically linked to `gpa` (unlike `score_final`).

**Why is this useful?**

* Expected to be the strongest predictor ($R^2$ likely $0.7 - 0.9$).

* Establishes the ceiling for this dataset.

* The gap $R^2(\text{FS-B}) - R^2(\text{FS-A})$ quantifies "how much does academic history add beyond demographics?"

### 4.3 Excluded from both FS

| Column | Reason | Doc | 
| ----- | ----- | ----- | 
| `score_final` | Algebraic leak | §3.2 | 
| `score_change` | Indirect leak | §3.2 | 
| `n_assessments` | Zero variance | §3.4 | 
| `source` | Zero variance | §3.4 | 
| `school`, `address` | Collinear with city | §3.3 | 
| `record_id`, `student_id` | Identifier | §3.1 | 
| `name` | Text, no signal | §3.1 | 

### 4.4 OneHotEncoder Contract (per-fold)

Categorical encoding must be fold-local — fitting on the full dataset before splitting would leak test-set category frequencies into training. The preprocessor is therefore rebuilt and refit on every fold's `X_train`, then `.transform()`-ed (not refit) on `X_test`.

**Configuration:**

| Parameter | Value | Reason | 
| ----- | ----- | ----- | 
| `handle_unknown` | `"ignore"` | always. A small fold may miss a category (e.g., MS-R absent from train). Prevents `ValueError` at predict time; unknown $\to$ all-zeros row. | 
| `drop` | `"first"` | always. Drops one dummy per categorical to eliminate the perfect-collinearity trap (the "dummy variable trap"). Makes LinearRegression design matrix full-rank. | 
| `sparse_output` | `False` | All models. Dense output is used uniformly: (a) sklearn's LinearRegression/Ridge accept sparse but their `.coef_` inspection is cleaner with dense arrays; (b) RF/GBM ignore zero blocks either way, so the memory saving is negligible at $N=1044$ ($\approx 836 \times 9$ per fold). Uniform choice keeps a single preprocessor per fold. | 

**Encoded column names:**

```
pre.get_feature_names_out()
# FS-A → ['num__attendance_rate', 'num__age',
#         'cat__gender_Female', 'cat__city_GP-R', 'cat__city_MS-U',
#         'cat__city_MS-R', 'cat__course_portuguese']
# FS-B → same + ['num__score_1', 'num__score_2']

```

Column order is deterministic (`num` before `cat`, alphabetical within each transformer) — this is asserted by a regression test so that feature-importance CSVs remain comparable across folds.

**Deterministic seed:** OneHotEncoder is deterministic by itself. No `random_state` needed here (unlike KFold, which needs one for `shuffle=True`).

## 5. CV Strategy

### 5.1 Primary — `GroupKFold(5)`

**Rationale:** The Silver dataset has 662 unique students across 1,044 rows. A naive `KFold(shuffle=True)` could place the same student's math row in train and portuguese row in test. Because those two rows share nearly identical age, gender, city, and attendance, the model would appear to generalize when it is actually memorizing student-level identity.

**Implementation:**

```
from sklearn.model_selection import GroupKFold

cv = GroupKFold(n_splits=5)
groups = df["student_id"]  # 662 unique values

for fold, (tr, te) in enumerate(cv.split(X, y, groups=groups)):
    # Guarantee: set(df.iloc[tr]["student_id"]).isdisjoint(
    #              df.iloc[te]["student_id"])
    ...

```

**Properties:**

| Property | Value | 
| ----- | ----- | 
| `n_splits` | 5 | 
| `shuffle` | N/A (GroupKFold has none) | 
| Fold size | $\approx 209$ rows each ($1,044 / 5$) | 
| Group distribution | $\approx 132$ students per fold ($662 / 5$) | 

Enforced by test: `test_no_student_id_leakage_v2` — asserts no `student_id` appears in both train and test of any fold. This is the single most important correctness test in B.7.

### 5.2 Secondary — `KFold(5, shuffle=True, random_state=42)`

**Purpose:** quantify the leak. Comparing `KFold(5)` results vs `GroupKFold(5)` results reveals how much optimism the naive split introduces. If $\text{MAE}(\text{KFold}) \ll \text{MAE}(\text{GroupKFold})$, the leak is real.

### 5.3 Tertiary — LeaveOneOut (for v1 $\leftrightarrow$ v2 comparability only)

Day 1 used LOO. To enable apples-to-apples comparison of the pipeline (not the dataset), v2 also runs LOO. This is not the primary metric — it is a bridge to Day 1's numbers.

**Implementation note (cost):** LOO yields 1,044 folds per feature set. Running RF ($\approx 0.5$ s/fit) and GBM ($\approx 1$ s/fit) would need $\approx 26$ min per FS. LOO is therefore restricted to `{baseline, linear, ridge}` — the same models v1 used. `GroupKFold(5)` is the primary scheme for tree models.

### 5.4 Quaternary — `GroupKFold(3)`

**Sanity check:** does the fold count matter? If GKF3 and GKF5 diverge wildly, the CV estimate is unstable (bad sign for a dataset this size).

### 5.5 CV summary table

| \# | Scheme | Folds | Shuffle | Primary? | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | `GroupKFold(5)` | 5 | No | ✅ YES | 
| 2 | `KFold(5)` | 5 | Yes (seed=42) | 🟡 comparison | 
| 3 | `LeaveOneOut` | 1,044 | No | 🟡 v1 bridge | 
| 4 | `GroupKFold(3)` | 3 | No | 🟡 stability check | 

Total CV configurations: 4.

## 6. Models

### 6.1 `DummyRegressor(strategy="mean")` — baseline

* Reused from v1 (`src.ml.baseline`).

* Lower bound: any model must beat it to be considered useful.

* With `GroupKFold(5)`, the baseline will fluctuate across folds (each fold's train mean differs) — reported as mean $\pm$ std.

### 6.2 `LinearRegression`

* Reused from v1 (`src.ml.trainer.make_linear`).

* Risk at $N=1044$: mild multicollinearity among OneHot dummies (`city` has 4 levels $\to 1$ dummy is redundant). `drop='first'` (§4.4) eliminates this; coefficients become stable.

### 6.3 `Ridge($\alpha=1.0$)`

* Reused from v1.

* At $N=1044$, $\alpha=1.0$ is no longer over-regularized (Day 1's finding was specific to $N=8$ per fold). Expect Ridge $\approx$ Linear here.

* No $\alpha$-sweep in B.7 (deferred to B.8).

### 6.4 `RandomForestRegressor` — NEW

```
RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
)

```

* **Why:** handles non-linearities and interactions automatically.

* Features like `attendance_rate` may have threshold effects.

* **Output:** `feature_importances_` (Gini importance) — $7-9$ values per fold.

* **Risk:** with 662 groups across 5 folds, each fold's train sees $\approx 836$ rows. RF will not overfit badly at this scale.

* **Hyperparameters:** defaults chosen for the B.7 baseline; `n_estimators`, `max_depth`, `min_samples_leaf` tuning is deferred to B.8 (documented as non-goal in §1).

### 6.5 `GradientBoostingRegressor` — NEW

```
GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=3,
    random_state=42,
)

```

* **Why:** typically outperforms RF on tabular regression, especially with moderate $N$. Slow training is acceptable (single dataset).

* **Risk:** more sensitive to hyperparameters than RF; default settings are documented as "not tuned."

* **Hyperparameters:** defaults chosen for the B.7 baseline; `learning_rate`, `n_estimators`, `max_depth` tuning is deferred to B.8 (documented as non-goal in §1).

### 6.6 Not used (and why)

| Model | Reason | 
| ----- | ----- | 
| `Lasso` | Performs feature selection — would hide multicollinearity signal we want to keep visible in FS-B. | 
| `ElasticNet` | Premature before we know whether Ridge alone works. | 
| `XGBoost / LightGBM` | External dep; sklearn's GBM is sufficient for B.7. | 
| `SVR` | Slow at $N=1044$ without careful kernel choice. | 
| Neural nets | Out of scope (documented in `ML_EXPERIMENTS.md` §1). | 

Total models: 5 (baseline + 4 learners).

## 7. Metrics

Same trio as v1 (`src.ml.metrics`), reused unchanged:

| Metric | Formula | Unit | Interpretation | 
| ----- | ----- | ----- | ----- | 
| MAE | $\text{mean}(\vert y - \hat{y} \vert)$ | GPA points | Typical error | 
| RMSE | $\sqrt{\text{mean}((y - \hat{y})^2)}$ | GPA points | Penalizes large errors | 
| $R^2$ | $1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}$ | unitless | Variance explained | 

**Additional (v2-only):**

* Feature importance — for RF and GBM, from `.feature_importances_`.

* Encoded feature names — from `OneHotEncoder.get_feature_names_out()`.

* $\Delta \text{MAE}$ vs baseline — per (CV, model, FS) cell.

$R^2$ **behavior at** $N=1044$**:**

* Not NaN (all folds have $n_{\text{test}} \ge 200$).

* Not wildly negative (small-sample $\text{SS}_{\text{tot}}$ problem disappears).

* Expected: $0.3 - 0.6$ for FS-A, $0.7 - 0.9$ for FS-B (documented as expected, not asserted).

## 8. File Plan

```
docs/
└── ML_EXPERIMENTS_SCALE.md           ← this file (B.7.1)
src/ml/                               ← v2 additions (additive, not replacement)
├── data_v2.py                        ← B.7.2 — load silver, filter uci, FS-A/FS-B
├── split_v2.py                       ← B.7.3 — 4 CV schemes
├── trainer_v2.py                     ← B.7.4 — + RF + GBM
└── pipeline_v2.py                    ← B.7.5 — orchestrator
scripts/
└── run_ml_pipeline_v2.py             ← B.7.6 — CLI
tests/
└── test_ml_v2.py                     ← B.7.7 — 37 tests
data/gold/                            ← gitignored, regenerable
├── model_metrics_v2.csv              ← per-fold raw
├── model_metrics_v2.json             ← summary
└── feature_importance_v2.csv         ← RF + GBM per fold

Frozen (must not change):
- src/ml/* (v1 — Day 1)
- data/gold/ml_features.parquet (9 rows)
- src/features/engineering.py
- src/warehouse/star_schema.py

```

## 9. Success Criteria

| \# | Criterion | Verification | 
| ----- | ----- | ----- | 
| 1 | `docs/ML_EXPERIMENTS_SCALE.md` exists | this file | 
| 2 | `src/ml/{data,split,trainer,pipeline}_v2.py` exist | `ls src/ml/` | 
| 3 | `data_v2.load_uci_only()` returns exactly 1,044 rows | test | 
| 4 | `data_v2` asserts no `score_final` / `score_change` in any FS | test | 
| 5 | `split_v2.make_group_kfold_5()` — no group crosses folds | test | 
| 6 | 36 experimental cells (GKF5 + KFold5 + GKF3 = 30; LOO = 6) | CSV inspection | 
| 7 | MAE / RMSE / $R^2$ reported for all 36 cells | CSV inspection | 
| 8 | Feature importance saved for RF + GBM | file check | 
| 9 | $269 \to 299$ tests ($+30$) | `pytest tests/ -q` | 
| 10 | CI remains 🟢 on py3.11/3.12/3.13 | GitHub Actions | 
| 11 | v1 artifacts unchanged | `git diff src/ml/*.py` | 
| 12 | `ml_features.parquet` unchanged | `git diff` | 
| 13 | No leaky feature in any result | `test_no_leaky_features_v2` | 

**Note on criterion #6 — "36 cells" vs CSV row count:**
36 refers to summary cells $(\text{CV scheme} \times \text{model} \times \text{feature-set})$, not CSV rows. LOO contributes 6 cells (3 models, not 5 — see §5.3). The raw `model_metrics_v2.csv` stores one row per fold:

$$
\text{GroupKFold5}: 5 \times 5 \times 2 = 50
$$

$$
\text{KFold5}: 5 \times 5 \times 2 = 50
$$

$$
\text{GroupKFold3}: 3 \times 5 \times 2 = 30
$$

$$
\text{LeaveOneOut}: 1{,}044 \times 3 \times 2 = 6{,}264
$$

$$
\textbf{Total} = \mathbf{6{,}394 \text{ rows}}
$$


The summary JSON collapses these into 36 cells (mean ± std per cell).

## 10. Risks & Mitigations

| \# | Risk | Likelihood | Impact | Mitigation | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | `GroupKFold` silently leaks a student | Low | Critical | `test_no_student_id_leakage_v2` — asserts disjoint group sets | 
| 2 | `score_final` reintroduced by refactor | Medium | Critical | `test_no_leaky_features_v2` — asserts absence | 
| 3 | FS-A $R^2 \approx 0 \to$ "the model failed" | Medium | Medium | Expected; report honestly. FS-B is the real baseline | 
| 4 | Linear/Ridge singular design matrix | Low | Medium | `city` only + `drop='first'` (§4.4) | 
| 5 | RF/GBM training too slow for CI | Low | Low | UCI is small ($\sim 1\text{K}$ rows); RF $\approx 3\text{s}$, GBM $\approx 10\text{s}$ locally | 
| 6 | Different Python versions give different RF results | Low | Low | `random_state=42` fixed; `n_jobs=-1` may reorder but not change output | 
| 7 | 36 experiments overwhelms reading | Medium | Low | Summary in JSON; raw fold-level in CSV | 
| 8 | Memory during pipeline (pandas copy) | Low | Low | $1044 \times 9 \approx 75\text{ KB}$ — negligible | 
| 9 | Cross-source `student_id` collisions | Low | Medium | Filter `source == "uci"` at load — collisions are eliminated | 
| 10 | Non-determinism from age | Low | Low | `REFERENCE_DATE` unchanged (2026-10-10) — same as v1 | 
| 11 | OneHot `drop='first'` differs across folds | Low | Low | Deterministic ordering; `handle_unknown='ignore'` covers missing categories | 

## 11. Findings (2026-10-11)

### 11.1 Hypothesis Results (H1–H6)

All six pre-registered hypotheses were confirmed at $N=1,044$.

| \# | Hypothesis | Result | Evidence | 
| ----- | ----- | ----- | ----- | 
| H1 | FS-B $\gg$ FS-A ($\Delta R^2 > 0.3$) | ✅ | Best FS-A $R^2=0.1115$, best FS-B $R^2=0.8723$, $\Delta=0.761$ | 
| H2 | $\text{GBM} \ge \text{RF} \ge \text{Linear}$ on FS-B | ✅ | MAE: GBM 0.1724 < RF 0.1756 < Linear 0.1902 (GKF5) | 
| H3 | $\text{MAE}(\text{GroupKFold}) \ge \text{MAE}(\text{KFold})$ | ✅ (weakly) | FS-B GKF5=0.1724 vs KFold5=0.1705 ($\Delta=0.0019$) | 
| H4 | $\text{Ridge} \approx \text{Linear}$ at $N=1044$ | ✅ | FS-B: Ridge 0.1876 vs Linear 0.1902 ($\Delta=0.0026$) | 
| H5 | `score_2` dominates FS-B importances | ✅ | RF 0.851, GBM 0.870 | 
| H6 | `attendance_rate` dominates FS-A importances | ✅ | RF 0.341, GBM 0.352 | 

### 11.2 Primary Results — `GroupKFold(5)`

The primary scheme (docs §5.1). Mean ± std across 5 folds.

| FS | Model | MAE | RMSE | $R^2$ | 
| ----- | ----- | ----- | ----- | ----- | 
| FS-A | Baseline | $0.5656 \pm 0.038$ | $0.7710 \pm 0.059$ | $-0.0015$ | 
| FS-A | Linear | $0.5438 \pm 0.028$ | $0.7433 \pm 0.049$ | $0.0672$ | 
| FS-A | Ridge | $0.5440 \pm 0.028$ | $0.7432 \pm 0.049$ | $0.0675$ | 
| FS-A | RandomForest | $0.5635 \pm 0.032$ | $0.7496 \pm 0.049$ | $0.0479$ | 
| FS-A | GradientBoosting | $0.5448 \pm 0.026$ | $0.7241 \pm 0.038$ | $0.1115$ | 
| FS-B | Baseline | $0.5656 \pm 0.038$ | $0.7710 \pm 0.059$ | $-0.0015$ | 
| FS-B | Linear | $0.1902 \pm 0.017$ | $0.3071 \pm 0.043$ | $0.8411$ | 
| FS-B | Ridge | $0.1876 \pm 0.018$ | $0.3070 \pm 0.044$ | $0.8413$ | 
| FS-B | RandomForest | $0.1756 \pm 0.020$ | $0.2861 \pm 0.038$ | $0.8618$ | 
| FS-B | GradientBoosting | $0.1724 \pm 0.014$ | $0.2754 \pm 0.033$ | $0.8723$ | 

**Reading:** Under the primary scheme, GBM wins on FS-B with MAE $\approx 0.17$ GPA points. The baseline (mean predictor) is indistinguishable across FS — it ignores $X$ — MAE $\approx 0.57$.

### 11.3 v1 ($N=9$) vs v2 ($N=1,044$) — Head-to-Head

| Metric | v1 (LOO, $N=9$) | v2 (GKF5, $N=1044$, FS-B) | $\Delta$ | Interpretation | 
| ----- | ----- | ----- | ----- | ----- | 
| Baseline MAE | 0.340 | 0.566 | $+0.226$ | v1's baseline was optimistic | 
| Linear MAE | 0.120 ⭐ | 0.190 | $+0.070$ | v1's 0.120 was small-sample luck | 
| Ridge(1.0) MAE | 0.297 | 0.188 | $-0.109$ | Over-regularization disappeared | 
| $R^2$ (Linear) | NaN | 0.841 | — | $R^2$ defined at $N=1044$ | 
| Best model | Linear | GBM | — | Trees need $N \ge 100$ | 

*Note:* v1's "Linear MAE = 0.120" was not a real result — with $N_{\text{train}}=8$ per LOO fold, the model essentially memorized the single test point. v2's numbers are the first statistically meaningful ones.

### 11.4 Cross-CV Stability

FS-B / GBM across 4 schemes:

| CV Scheme | MAE | Notes | 
| ----- | ----- | ----- | 
| `GroupKFold(5)` — primary | 0.1724 | Reference | 
| `KFold(5)` | 0.1705 | Slightly optimistic (leak) | 
| `GroupKFold(3)` | 0.1753 | Slightly pessimistic | 
| `LeaveOneOut` | — | Not run for trees (see §5.3) | 

Spread: 0.1705–0.1753, i.e., $\pm 1.5\%$ of the reference. Very stable.

### 11.5 Feature Importance (RF + GBM, GKF5)

**FS-A — demographic-only:**

| Feature | RF | GBM | 
| ----- | ----- | ----- | 
| `attendance_rate` | 0.341 | 0.352 | 
| `age` | 0.271 | 0.233 | 
| `gender_Male` | 0.103 | 0.078 | 
| `course_portuguese` | 0.091 | 0.156 | 
| `city_GP-U` | 0.087 | 0.075 | 

**FS-B — with prior grades:**

| Feature | RF | GBM | 
| ----- | ----- | ----- | 
| `score_2` | 0.851 | 0.870 | 
| `attendance_rate` | 0.070 | 0.069 | 
| `score_1` | 0.019 | 0.033 | 
| `course_portuguese` | 0.016 | 0.013 | 
| `age` | 0.024 | 0.011 | 

**Reading:**

* In FS-A, information is spread across 5+ features — no single dominant signal.

* In FS-B, `score_2` (G2 — second period grade) absorbs $\sim 86\%$ of importance; all other features collapse to noise.

* `attendance_rate` remains the strongest non-grade signal in both sets.

### 11.6 Key Scientific Takeaways

1. **Demographics alone are weak predictors.** FS-A tops out at $R^2 \approx 0.11$. Gender, city, age, and attendance explain only $\sim 1/10$ of GPA variance.

2. **Prior grades dominate.** FS-B (adding G1, G2) jumps $R^2$ to 0.87. G2 alone carries $\sim 86\%$ of tree importance — GPA in period 3 is largely determined by performance in period 2.

3. **Trees shine once** $N$ **is adequate.** At $N=9$, trees were impossible; at $N=1,044$, GBM beats linear by $\sim 0.018$ MAE ($\approx 10\%$ relative improvement). Small but consistent.

4. **GroupKFold matters marginally but importantly.** The KFold-vs-GroupKFold gap in MAE is tiny (0.0019), but the correctness guarantee (no student in train $\cap$ test) is what we bought — not the metric shift.

5. **Ridge stops being harmful at scale.** v1's $\text{Ridge}(\alpha=1.0)$ was $2.5 \times$ worse than Linear ($N_{\text{train}}=8$). At $N_{\text{train}} \approx 836$, Ridge matches Linear to within 0.003 MAE.

### 11.7 Persisted Artifacts

Regenerable via:

```
python scripts/run_ml_pipeline_v2.py

```

Elapsed: $\sim 87$s (Windows 11, single machine).

| File | Rows | Size | Contents | 
| ----- | ----- | ----- | ----- | 
| `data/gold/model_metrics_v2.csv` | 6,394 | 240 KB | Per-fold raw metrics | 
| `data/gold/model_metrics_v2.json` | 36 cells | 13 KB | Summary (mean ± std) | 
| `data/gold/feature_importance_v2.csv` | 416 | 19 KB | RF + GBM per-fold importances | 

All three are gitignored (regenerable).

## 12. Traceability

| Decision | Curriculum Guide Reference | Chapter / Section | 
| ----- | ----- | ----- | 
| Leakage re-audit (17 cols) | Unit 9 (pp. 76-77) | Ch 9 §3 | 
| FS-A $\to$ demographic-only baseline | Applied ML Day 1 (California Housing) — prequel reference | — §4.1 | 
| FS-B $\to$ temporal signal augmentation | Applied ML Day 1 (California Housing) — prequel reference | — §4.2 | 
| Multicollinearity ($\text{city} \supset \text{school} \cup \text{address}$) | Unit 9 | — §3.3 | 
| Zero-variance exclusion | Unit 9 | — §3.4 | 
| GroupKFold | Applied ML Day 1 (California Housing) — prequel reference | — §5.1 | 
| Tree ensembles (RF, GBM) | Applied ML Day 1 (California Housing) — prequel reference | — §6.4, §6.5 | 
| OneHot `drop='first'` | Unit 9 | — §4.4 | 
| Add a layer, don't replace | — | Ch 12 §8 | 
| Documentation-first | Unit 11 | Ch 12 this file | 
| Determinism (`REFERENCE_DATE`) | Unit 10 (p. 17) | — §10 (#10) | 
| Pre-registered hypotheses | — | Ch 12 §11.2 | 

## 13. Version History

| Version | Date | Change | 
| ----- | ----- | ----- | 
| v0.1 | 2026-10-11 | Initial draft after Silver Merge (B.6) | 
| v0.2 | 2026-10-11 | Fix §2.1 source counts (77 rows, not 92); add §4.4 OneHotEncoder Contract; clarify §9 #6 cells-vs-rows; add hyperparameter-justification to §6.4/§6.5; disambiguate Applied ML Day 1 reference in §12 | 
| v1.0 | 2026-10-11 | Update §11 with empirical findings from Phase B.7 execution ($N=1,044$) | 

## 14. References

| Ref | Source | 
| ----- | ----- | 
| `docs/ML_EXPERIMENTS.md` | Day 1 — $N=9$ baseline, LOO, leakage audit | 
| `docs/SILVER_MERGE.md` | Phase B.6 — 8-source unification | 
| `docs/UCI_ETL.md` | Phase B.5 — UCI $\to$ unified schema | 
| `docs/DATA_SOURCES.md` | §7 — GroupKFold rationale | 
| `docs/HANDOFF_v8.md` | Project state at B.7 entry | 
| UCI dataset 320 | https://archive.ics.uci.edu/dataset/320 | 
| Cortez & Silva 2008 | "Using Data Mining to Predict Secondary School Student Performance" | 
| Unit 9 | Data Quality (leakage, §76-77) | 
| Unit 10 | Determinism / Reproducibility | 
| Guide Ch 9 | Leakage & CV | 
| Guide Ch 12 | Repeatable / Resilient / Scalable | 

**Last Updated:** 2026-10-11

**Status:** ✅ Complete

**Next Step:** B.7.7 complete — Phase B.7 done. Next: Phase C (Docs Polish)