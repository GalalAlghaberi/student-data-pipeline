# ML Experiments — Phase B.7 (Scale-Up) / تجارب تعلّم الآلة — المرحلة B.7 (التوسّع إلى $N=1044$)

**Version:** v4.3.0-dev  
**Baseline:** a9c4e6b (Phase B.6 complete)  
**Status:** 🔵 Planned → In Progress  
**Reference:** `docs/ML_EXPERIMENTS.md` (Day 1, $N=9$) + `docs/SILVER_MERGE.md`  
**Author:** Galal Al-Ghaberi  
**Date:** 2026-10-11  

---

## 1. Objective

Scale the ML layer from **$N=9$** (Day 1, synthetic features) to **$N=1044$** (Phase B.5 UCI rows) using the Phase B.6 Silver dataset (`data/silver/unified_students.parquet`), while preserving every existing artifact (`src/ml/*`, `ml_features.parquet`, 269 tests).

**Primary goals:**
1. Replace **LeaveOneOut** (mandatory at $N=9$) with **GroupKFold(5)** to enforce student-level isolation.
2. Introduce **tree-based models** (RandomForest, GradientBoosting) — impossible at $N=9$.
3. Report **honest feature importance** at scale.
4. Compare **v1 ($N=9$)** vs **v2 ($N=1044$)** head-to-head.

**Educational goals:**
- Practice **leakage re-audit** on a wider schema (17 columns).
- Introduce **group-aware CV** — a transferable concept.
- Demonstrate **multicollinearity detection** (city vs school+address).
- Demonstrate **ablation** (FS-A vs FS-B).

**Non-goals:**
- Modifying `src/ml/*` (v1) — Golden Rule 1.
- Modifying `ml_features.parquet` (9 rows — FROZEN).
- Hyperparameter tuning beyond a documented baseline (deferred to B.8).
- Deep learning.

---

## 2. Dataset

| Property | Value |
|---|---|
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
|---|---|---|
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
|---|---|
| `gender`, `course`, `school`, `address` = NaN | all 7 base sources |
| `score_1`, `score_2`, `score_final` = NaN | all 7 base sources |
| `n_assessments` = NaN | all 7 base sources |
| `gpa` = NaN | api, postgres, sqlite (46 rows) |

Including them would require 8+ imputation strategies, each with its own bias. The Silver layer is honest about this (see `quality_report.json`) — but the ML layer must decide, and the honest decision is **UCI-only**.

**Decision:** filter `df["source"] == "uci"` at load time. Documented as a design choice, not a silent drop.

### 2.2 Filtering pipeline

```python
df_silver = pd.read_parquet("data/silver/unified_students.parquet")
df_uci    = df_silver[df_silver["source"] == "uci"].copy()
# Sanity: len(df_uci) == 1044; df_uci["gpa"].notna().all() == True
```

---

## 3. Leakage Re-Audit (CRITICAL — Unit 9, pp. 76-77)

The Silver schema exposes 17 columns vs Day 1's 15. A full re-audit is mandatory before any feature is selected.

### 3.1 Column-by-column verdict

| # | Column | Formula / Source | Verdict |
|---|---|---|---|
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
$$\text{In UCI\_ETL.md } \S 4.1: \quad gpa = \frac{G3}{5.0}, \quad \text{score\_final} = G3 \implies gpa = \frac{\text{score\_final}}{5.0}$$

Using `score_final` to predict `gpa` is predicting $5 \times gpa$ from $gpa$. This is the exact analogue of Day 1's `avg_score` leakage (`ML_EXPERIMENTS.md` §3.1). $R^2$ would be exactly 1.0 with a trivial model.

**`score_change` (row 11) — indirect leak:**
$$\text{score\_change} = \text{score\_final} - \text{score\_1} = 5 \times gpa - \text{score\_1}$$

Predicting `gpa` from `score_change` is predicting `gpa` from $5 \times gpa - \text{score\_1}$. Still a direct algebraic dependency on the target.

**Verdict:** both `score_final` and `score_change` are forbidden in every feature set. A regression test (`test_no_leaky_features_v2`) will assert this.

### 3.3 Multicollinearity: city $\supset$ school $\cup$ address

The UCI ETL defines:
$$\text{city} = \text{"\{school\}-\{address\}"} \quad (\text{e.g., "GP-U", "GP-R", "MS-U", "MS-R"})$$

Therefore:
- $\text{school} \in \{\text{GP, MS}\} \to 2$ levels
- $\text{address} \in \{\text{U, R}\} \to 2$ levels
- $\text{school} \times \text{address} \to 4$ combinations = city's 4 levels

Including all three would give the encoder:
- `city` (OneHot $\to 4$ dummies)
- `school` (OneHot $\to 2$ dummies, perfectly determined by city)
- `address` (OneHot $\to 2$ dummies, perfectly determined by city)

This creates a singular design matrix — `LinearRegression` would silently pick an arbitrary solution among infinitely many, and feature importances would be meaningless.

**Decision:** use `city` only in feature sets. Keep `school` and `address` as preserved columns (not dropped from the parquet) for future analytical use, but exclude them from every FS.

### 3.4 `source` and `n_assessments`: zero variance

Both columns are constant over UCI-only rows:
- `source == "uci"` for $1044 / 1044$ rows.
- `n_assessments == 3` for $1044 / 1044$ rows (math + por each have G1, G2, G3).

Zero-variance columns:
- Are dropped by sklearn's `VarianceThreshold(0.0)` silently.
- Contribute 0 to every model.
- Pollute feature-importance tables with $0.0000$.

**Decision:** exclude both from every FS. `source` remains in the parquet (needed for filtering); `n_assessments` is kept for traceability but not used.

### 3.5 Forbidden patterns (documented)

```python
# ❌ WRONG — score_final leaks the target
X = df[["score_final", "age"]]
y = df["gpa"]
# R² will be 1.0, model is useless

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

---

## 4. Feature Sets (FS-A, FS-B)

Two feature sets are evaluated in parallel. This is a deliberate ablation study — not indecision.

### 4.1 FS-A — Demographic-only baseline

Hypothesis: How much can be predicted from non-academic context?

| Feature | Type | Range / Values | Source |
|---|---|---|---|
| `attendance_rate` | numeric | $[0.744, 1.000]$ | absences |
| `age` | numeric | $[15, 22]$ | direct |
| `gender` | categorical | $\{\text{Male, Female}\}$ | sex |
| `city` | categorical | $\{\text{GP-U, GP-R, MS-U, MS-R}\}$ | school+address |
| `course` | categorical | $\{\text{math, portuguese}\}$ | filename |

Total: 3 numeric + 3 categorical $\to$ OneHot $\to$ 7 encoded columns.

**Why this set:**
- All features are context; none are grades.
- If $R^2$ is high, demographics alone "explain" GPA — a controversial but often-observed result in education data.
- If $R^2$ is near zero, GPA genuinely requires academic history.

### 4.2 FS-B — Temporal signal augmentation

FS-A + the two prior-period grades:

| Feature | Type | Range | Note |
|---|---|---|---|
| `score_1` | numeric | $[0, 20]$ | G1 — first period |
| `score_2` | numeric | $[0, 20]$ | G2 — second period |

Total: 5 numeric + 3 categorical $\to$ OneHot $\to$ 9 encoded columns.

**Why is this legal?**
- `score_1` and `score_2` are prior measurements, not the target.
- They are conceptually "grades before the final exam" — a real predictor a school would legitimately have when trying to forecast final GPA.
- They are NOT algebraically linked to `gpa` (unlike `score_final`).

**Why is this useful?**
- Expected to be the strongest predictor ($R^2$ likely $0.7 - 0.9$).
- Establishes the ceiling for this dataset.
- The gap $R^2(\text{FS-B}) - R^2(\text{FS-A})$ quantifies "how much does academic history add beyond demographics?"

### 4.3 Excluded from both FS

| Column | Reason | Doc |
|---|---|---|
| `score_final` | Algebraic leak | §3.2 |
| `score_change` | Indirect leak | §3.2 |
| `n_assessments` | Zero variance | §3.4 |
| `source` | Zero variance | §3.4 |
| `school`, `address` | Collinear with city | §3.3 |
| `record_id`, `student_id` | Identifier | §3.1 |
| `name` | Text, no signal | §3.1 |

### 4.4 OneHotEncoder Contract (per-fold)

Categorical encoding must be fold-local — fitting on the full dataset before splitting would leak test-set category frequencies into training. The preprocessor is therefore rebuilt and refit on every fold's `X_train`, then `.transform()`-ed (not refit) on `X_test`.

Configuration:

| Parameter | Value | Reason |
|---|---|---|
| `handle_unknown` | `"ignore"` | always. A small fold may miss a category (e.g., MS-R absent from train). Prevents ValueError at predict time; unknown $\to$ all-zeros row. |
| `drop` | `"first"` | always. Drops one dummy per categorical to eliminate the perfect-collinearity trap (the "dummy variable trap"). Makes LinearRegression design matrix full-rank. |
| `sparse_output` | `False` | for Linear, Ridge. Dense is required: sklearn's LinearRegression and Ridge accept sparse, but downstream `.coef_` inspection and RF/GBM feature-name mapping are cleaner with dense arrays. |
| `sparse_output` | `True` | for RF, GBM. Trees ignore zero blocks efficiently; sparse saves memory and speeds up training. Fold size $\sim 836$ rows $\times 9$ cols is trivially small either way — the choice is documented for consistency with future larger datasets. |

Encoded column names:
```python
pre.get_feature_names_out()
# FS-A → ['num__attendance_rate', 'num__age',
#         'cat__gender_Female', 'cat__city_GP-R', 'cat__city_MS-U',
#         'cat__city_MS-R', 'cat__course_portuguese']
# FS-B → same + ['num__score_1', 'num__score_2']
```

Column order is deterministic (num before cat, alphabetical within each transformer) — this is asserted by a regression test so that feature-importance CSVs remain comparable across folds.

Deterministic seed: OneHotEncoder is deterministic by itself. No `random_state` needed here (unlike KFold, which needs one for `shuffle=True`).

---

## 5. CV Strategy

### 5.1 Primary — GroupKFold(5)

Rationale: The Silver dataset has 662 unique students across 1,044 rows. A naive `KFold(shuffle=True)` could place the same student's math row in train and portuguese row in test. Because those two rows share nearly identical age, gender, city, and attendance, the model would appear to generalize when it is actually memorizing student-level identity.

Implementation:
```python
from sklearn.model_selection import GroupKFold
cv = GroupKFold(n_splits=5)
groups = df["student_id"]  # 662 unique values
for fold, (tr, te) in enumerate(cv.split(X, y, groups=groups)):
    # Guarantee: set(df.iloc[tr]["student_id"]).isdisjoint(
    #              df.iloc[te]["student_id"])
    ...
```

Properties:

| Property | Value |
|---|---|
| `n_splits` | 5 |
| `shuffle` | N/A (GroupKFold has none) |
| Fold size | $\approx 209$ rows each ($1,044 / 5$) |
| Group distribution | $\approx 132$ students per fold ($662 / 5$) |

Enforced by test: `test_no_student_id_leakage_v2` — asserts no `student_id` appears in both train and test of any fold. This is the single most important correctness test in B.7.

### 5.2 Secondary — KFold(5, shuffle=True, random_state=42)

Purpose: quantify the leak. Comparing `KFold(5)` results vs `GroupKFold(5)` results reveals how much optimism the naive split introduces. If $\text{MAE}(\text{KFold}) \ll \text{MAE}(\text{GroupKFold})$, the leak is real.

### 5.3 Tertiary — LeaveOneOut (for v1 $\leftrightarrow$ v2 comparability only)

Day 1 used LOO. To enable apples-to-apples comparison of the pipeline (not the dataset), v2 also runs LOO. This is not the primary metric — it is a bridge to Day 1's numbers.

### 5.4 Quaternary — GroupKFold(3)

Sanity check: does the fold count matter? If GKF3 and GKF5 diverge wildly, the CV estimate is unstable (bad sign for a dataset this size).

### 5.5 CV summary table

| # | Scheme | Folds | Shuffle | Primary? |
|---|---|---|---|---|
| 1 | `GroupKFold(5)` | 5 | No | ✅ YES |
| 2 | `KFold(5)` | 5 | Yes (seed=42) | 🟡 comparison |
| 3 | `LeaveOneOut` | 1,044 | No | 🟡 v1 bridge |
| 4 | `GroupKFold(3)` | 3 | No | 🟡 stability check |

Total CV configurations: 4.

---

## 6. Models

### 6.1 `DummyRegressor(strategy="mean")` — baseline
- Reused from v1 (`src.ml.baseline`).
- Lower bound: any model must beat it to be considered useful.
- With `GroupKFold(5)`, the baseline will fluctuate across folds (each fold's train mean differs) — reported as mean $\pm$ std.

### 6.2 `LinearRegression`
- Reused from v1 (`src.ml.trainer.make_linear`).
- Risk at $N=1044$: mild multicollinearity among OneHot dummies (city has 4 levels $\to 1$ dummy is redundant). `drop='first'` (§4.4) eliminates this; coefficients become stable.

### 6.3 `Ridge($\alpha=1.0$)`
- Reused from v1.
- At $N=1044$, $\alpha=1.0$ is no longer over-regularized (Day 1's finding was specific to $N=8$ per fold). Expect Ridge $\approx$ Linear here.
- No $\alpha$-sweep in B.7 (deferred to B.8).

### 6.4 `RandomForestRegressor` — NEW
```python
RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
)
```
- Why: handles non-linearities and interactions automatically.
- Features like `attendance_rate` may have threshold effects.
- Output: `feature_importances_` (Gini importance) — $7-9$ values per fold.
- Risk: with 662 groups across 5 folds, each fold's train sees $\approx 836$ rows. RF will not overfit badly at this scale.
- Hyperparameters: defaults chosen for the B.7 baseline; `n_estimators`, `max_depth`, `min_samples_leaf` tuning is deferred to B.8 (documented as non-goal in §1).

### 6.5 `GradientBoostingRegressor` — NEW
```python
GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=3,
    random_state=42,
)
```
- Why: typically outperforms RF on tabular regression, especially with moderate $N$. Slow training is acceptable (single dataset).
- Risk: more sensitive to hyperparameters than RF; default settings are documented as "not tuned."
- Hyperparameters: defaults chosen for the B.7 baseline; `learning_rate`, `n_estimators`, `max_depth` tuning is deferred to B.8 (documented as non-goal in §1).

### 6.6 Not used (and why)

| Model | Reason |
|---|---|
| `Lasso` | Performs feature selection — would hide multicollinearity signal we want to keep visible in FS-B. |
| `ElasticNet` | Premature before we know whether Ridge alone works. |
| `XGBoost / LightGBM` | External dep; sklearn's GBM is sufficient for B.7. |
| `SVR` | Slow at $N=1044$ without careful kernel choice. |
| `Neural nets` | Out of scope (documented in `ML_EXPERIMENTS.md` §1). |

Total models: 5 (baseline + 4 learners).

---

## 7. Metrics

Same trio as v1 (`src.ml.metrics`), reused unchanged:

| Metric | Formula | Unit | Interpretation |
|---|---|---|---|
| MAE | $\text{mean}(|y - \hat{y}|)$ | GPA points | Typical error |
| RMSE | $\sqrt{\text{mean}((y - \hat{y})^2)}$ | GPA points | Penalizes large errors |
| $R^2$ | $1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}$ | unitless | Variance explained |

Additional (v2-only):
- Feature importance — for RF and GBM, from `.feature_importances_`.
- Encoded feature names — from `OneHotEncoder.get_feature_names_out()`.
- $\Delta \text{MAE}$ vs baseline — per (CV, model, FS) cell.

$R^2$ behavior at $N=1044$:
- Not NaN (all folds have $n_{\text{test}} \ge 200$).
- Not wildly negative (small-sample $\text{SS}_{\text{tot}}$ problem disappears).
- Expected: $0.3 - 0.6$ for FS-A, $0.7 - 0.9$ for FS-B (documented as expected, not asserted).

---

## 8. File Plan

```text
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
└── test_ml_v2.py                     ← B.7.7 — ~25 tests
data/gold/                            ← gitignored, regenerable
├── model_metrics_v2.csv              ← per-fold raw
├── model_metrics_v2.json             ← summary
└── feature_importance_v2.csv         ← RF + GBM per fold
```

**Frozen (must not change):**
- `src/ml/*` (v1 — Day 1)
- `data/gold/ml_features.parquet` (9 rows)
- `src/features/engineering.py`
- `src/warehouse/star_schema.py`

---

## 9. Success Criteria

| # | Criterion | Verification |
|---|---|---|
| 1 | `docs/ML_EXPERIMENTS_SCALE.md` exists | this file |
| 2 | `src/ml/{data,split,trainer,pipeline}_v2.py` exist | `ls src/ml/` |
| 3 | `data_v2.load_uci_only()` returns exactly 1,044 rows | test |
| 4 | `data_v2` asserts no `score_final` / `score_change` in any FS | test |
| 5 | `split_v2.make_group_kfold_5()` — no group crosses folds | test |
| 6 | 40 experimental cells ($4 \text{ CV} \times 5 \text{ models} \times 2 \text{ FS}$) | CSV inspection |
| 7 | MAE / RMSE / $R^2$ reported for all 40 cells | CSV inspection |
| 8 | Feature importance saved for RF + GBM | file check |
| 9 | $269 \to \sim 294$ tests ($+25$) | `pytest tests/ -q` |
| 10 | CI remains 🟢 on py3.11/3.12/3.13 | GitHub Actions |
| 11 | v1 artifacts unchanged | `git diff src/ml/*.py` |
| 12 | `ml_features.parquet` unchanged | `git diff` |
| 13 | No leaky feature in any result | `test_no_leaky_features_v2` |

**Note on criterion #6 — "40 cells" vs CSV row count:**  
40 refers to $(\text{CV scheme} \times \text{model} \times \text{feature-set})$ summary cells, not CSV rows. The raw `model_metrics_v2.csv` stores one row per fold, so its total length is:

$$\text{GroupKFold(5)} : 5 \text{ folds} \times 5 \text{ models} \times 2 \text{ FS} = 50 \text{ rows}$$
$$\text{KFold(5)} : 5 \text{ folds} \times 5 \text{ models} \times 2 \text{ FS} = 50 \text{ rows}$$
$$\text{LeaveOneOut} : 1044 \text{ folds} \times 5 \times 2 = 10440 \text{ rows}$$
$$\text{GroupKFold(3)} : 3 \text{ folds} \times 5 \text{ models} \times 2 \text{ FS} = 30 \text{ rows}$$
$$\textbf{Total} = \mathbf{10570 \text{ rows}}$$

The summary JSON collapses these into 40 cells (mean $\pm$ std per cell).

---

## 10. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | GroupKFold silently leaks a student | Low | Critical | `test_no_student_id_leakage_v2` — asserts disjoint group sets |
| 2 | `score_final` reintroduced by refactor | Medium | Critical | `test_no_leaky_features_v2` — asserts absence |
| 3 | FS-A $R^2 \approx 0 \to$ "the model failed" | Medium | Medium | Expected; report honestly. FS-B is the real baseline |
| 4 | Linear/Ridge singular design matrix | Low | Medium | `city` only + `drop='first'` (§4.4) |
| 5 | RF/GBM training too slow for CI | Low | Low | UCI is small ($\sim 1\text{K}$ rows); RF $\approx 3\text{s}$, GBM $\approx 10\text{s}$ locally |
| 6 | Different Python versions give different RF results | Low | Low | `random_state=42` fixed; `n_jobs=-1` may reorder but not change output |
| 7 | 40 experiments overwhelms reading | Medium | Low | Summary in JSON; raw fold-level in CSV |
| 8 | Memory during pipeline (pandas copy) | Low | Low | $1044 \times 9 \approx 75\text{ KB}$ — negligible |
| 9 | Cross-source `student_id` collisions | Low | Medium | Filter `source == "uci"` at load — collisions are eliminated |
| 10 | Non-determinism from age | Low | Low | `REFERENCE_DATE` unchanged (2026-10-10) — same as v1 |
| 11 | OneHot `drop='first'` differs across folds | Low | Low | Deterministic ordering; `handle_unknown='ignore'` covers missing categories |

---

## 11. Expected Findings (to be filled post-run)

### 11.1 Primary comparison: v1 vs v2

| Metric | v1 ($N=9$, LOO) | v2 ($N=1044$, GKF5) | $\Delta$ | Interpretation |
|---|---|---|---|---|
| Baseline MAE | 0.340 | TBD | TBD | More data $\to$ stabler mean |
| Linear MAE | 0.120 ⭐ | TBD | TBD | Small-sample luck may vanish |
| Ridge(1.0) MAE | 0.297 | TBD | TBD | Over-regularization should disappear |
| RandomForest MAE | — | TBD | — | New |
| GradientBoosting MAE | — | TBD | — | New |
| $R^2$ (Linear) | NaN | TBD | — | LOO $\to$ defined |

### 11.2 Expected hypotheses (declared before running — prevents HARKing)

| # | Hypothesis | Rationale | Status |
|---|---|---|---|
| H1 | FS-B $\gg$ FS-A ($\Delta R^2 > 0.3$) | G1/G2 carry strong signal | pending |
| H2 | GBM $\ge$ RF $\ge$ Linear on FS-B | Non-linearities + interactions | pending |
| H3 | $\text{MAE}(\text{GroupKFold}) \ge \text{MAE}(\text{KFold})$ | KFold leaks students | pending |
| H4 | Ridge $\approx$ Linear at $N=1044$ | Regularization effect shrinks | pending |
| H5 | `score_2` dominates FS-B importances | G2 is closest to G3 | pending |
| H6 | `attendance_rate` dominates FS-A importances | Strongest non-grade signal | pending |

Discipline: hypotheses are declared before running. If any fails, the failure is documented — not reframed.

### 11.3 Cross-scheme stability

| CV scheme | Expected MAE (FS-B, Linear) |
|---|---|
| `GroupKFold(5)` | baseline reference |
| `KFold(5)` | lower (optimistic) |
| `LeaveOneOut` | similar to GroupKFold but slower |
| `GroupKFold(3)` | higher variance |

---

## 12. Traceability

| Decision | Curriculum Guide Reference | Chapter / Section |
|---|---|---|
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

---

## 13. Version History

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-11 | Initial draft after Silver Merge (B.6) |
| v0.2 | 2026-10-11 | Fix §2.1 source counts (77 rows, not 92); add §4.4 OneHotEncoder Contract; clarify §9 #6 cells-vs-rows; add hyperparameter-justification to §6.4/§6.5; disambiguate Applied ML Day 1 reference in §12 |

---

## 14. References

| Ref | Source |
|---|---|
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
**Status:** 🔵 Planned → In Progress  
**Next Step:** B.7.2 — `src/ml/data_v2.py`  