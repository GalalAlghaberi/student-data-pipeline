# ML Experiments — Phase B (Day 1)
**Version:** v4.2.0-dev
**Baseline:** ad1b0c9 (Phase A complete)
**Status:** 🔵 Planned → In Progress
**Reference:** Applied ML Day 1 (California Housing) — adapted to Student Data
**Author:** Galal Al-Ghaberi
**Date:** 2026-10-10

---

## 1. Objective
Build the first ML layer on top of the Phase A feature store:
- **Target:** `gpa` (regression, continuous [0, 4])
- **Input:** `data/gold/ml_features.parquet` (9 rows × 15 columns)
- **Goal:** Demonstrate end-to-end ML pipeline (data → features → split → model → metrics)

**Educational purpose (Day 1 concepts):**
1. Data leakage prevention (Unit 9)
2. Cross-validation for small N
3. Baseline vs. LinearRegression vs. Ridge
4. MAE / RMSE / R² interpretation

**Non-goals:**
- Production deployment (Phase D)
- Deep learning / neural nets
- Hyperparameter tuning

---

## 2. Dataset

| Property | Value |
|---|---|
| Source | `data/gold/ml_features.parquet` (Phase A output) |
| Rows | 9 |
| Columns | 15 |
| Target | `gpa` (float [0, 4]) |
| Missing values | 0 (validated in Phase A) |

**⚠️ N=9 is extremely small.** This forces two decisions:
1. **LeaveOneOut CV** or **KFold(3)** — never simple train/test split.
2. **Ridge (L2)** is required, not optional, to prevent overfitting.

---

## 3. Leakage Audit (CRITICAL — Unit 9, pp. 76-77)

### 3.1 Mathematical verification
| Column | Formula | Verdict |
|---|---|---|
| `gpa` | **TARGET** | 🎯 target |
| `avg_score` | `gpa = avg_score / 25` | ❌ LEAKY |
| `academic_risk_score` | `(4 - gpa) + ...` — uses gpa directly | ❌ LEAKY |
| `performance_level` | `CASE WHEN avg_score >= 90 ...` | ❌ LEAKY |
| `city_score_gap` | `avg_score - median(avg_score in TRAIN)` | ❌ LEAKY |
| `city_rank` | `RANK() OVER (ORDER BY avg_score DESC)` | ❌ LEAKY |
| `attendance_rate` | `attendance / 100` — no gpa dependency | ✅ Safe |
| `n_assessments` | `COUNT(*)` — independent | ✅ Safe |
| `score_change` | `LAG(score) - score` — no gpa dependency | ✅ Safe |
| `date_of_birth` | → `age` (derived) | ✅ Safe |
| `gender` | categorical | ✅ Safe |
| `city` | categorical | ✅ Safe |
| `student_id` | ID | ⛔ excluded (not a feature) |
| `full_name` | text | ⛔ excluded (not a feature) |

**Result:** 5 leaky columns excluded, **6 safe features** retained (4 numeric + 2 categorical).

### 3.2 Why these 5 are leaky
1. **`avg_score`** — Algebraically: `gpa = avg_score / 25` (in `engineering.py`). Using it means predicting `gpa` from `gpa × 25`.
2. **`academic_risk_score`** — Its formula starts with `(4 - gpa)`. Direct leakage.
3. **`performance_level`** — `CASE WHEN avg_score >= 90 THEN 'Excellent' ...`. Since `avg_score = gpa × 25`, this is a discretized version of gpa.
4. **`city_score_gap`** — `avg_score - median(avg_score in TRAIN)`. Still rooted in avg_score.
5. **`city_rank`** — `RANK() OVER (ORDER BY avg_score DESC)`. Rank of avg_score.

### 3.3 Forbidden patterns (documented for future contributors)
```python
# ❌ WRONG — using leaky features
X = df[["avg_score", "academic_risk_score", "city_rank"]]
y = df["gpa"]
# R² will be ~0.99 but meaningless

# ✅ CORRECT — safe features only
X = df[["attendance_rate", "n_assessments", "score_change", "age", "gender", "city"]]
y = df["gpa"]
# R² will be modest but honest
```

## 4. Feature Set (Final)

### 4.1 Numeric (4)
| Feature | Range | Notes |
|---|---|---|
| attendance_rate | [0, 1] | attendance / 100 |
| n_assessments | ≥ 0 | count |
| score_change | ℝ | temporal delta |
| age | [16, 80] | derived from date_of_birth |

### 4.2 Categorical (2)
| Feature | Values | Notes |
|---|---|---|
| gender | {Male, Female} | |
| city | from dim_students.city.unique() | |

### 4.3 Determinism fix (age computation)
```python
REFERENCE_DATE: Final = pd.Timestamp("2026-10-10")
age = (REFERENCE_DATE - date_of_birth).days / 365.25
```
Why: Without a fixed reference date, age would change every day → break idempotency tests → non-reproducible results.

## 5. Cross-Validation Strategy
Constraint: N=9.

Why not train/test split?
- 80/20 split → 7 train + 2 test. Test set too small; variance would dominate.
- LOO uses 8 train + 1 test, 9 times — better use of data.

Chosen strategy: compare two CV schemes.

| Scheme | Folds | Train size per fold | Purpose |
|---|---|---|---|
| LeaveOneOut | 9 | 8 | Maximal data usage |
| KFold(3, shuffle=True, random_state=42) | 3 | 6 | Slightly more stable |

Deliverable: Report MAE / RMSE / R² for both schemes, for all 3 models. Compare ranges.

Not chosen (and why):
- TimeSeriesSplit — no temporal ordering in data.
- StratifiedKFold — classification-only.
- ShuffleSplit — similar issue to train/test split.

## 6. Models

### 6.1 Baseline — DummyRegressor(strategy="mean")
- Predicts the mean of y_train for every test sample.
- Purpose: Lower bound. If Linear/Ridge can't beat this, features have no signal.

### 6.2 LinearRegression
- `sklearn.linear_model.LinearRegression()`
- No regularization. With N=9 and 4 numeric features, coefficient estimate is unstable.

### 6.3 Ridge(α=1.0)
- `sklearn.linear_model.Ridge(alpha=1.0)`
- L2 regularization — required for N=9.
- α=1.0 is a documented default (no tuning in Day 1).

Not used:
- Lasso — performs feature selection, hides signal with so few features.
- RandomForest / GradientBoosting — overkill for N=9.

## 7. Metrics

| Metric | Formula | Unit | Interpretation |
|---|---|---|---|
| MAE | mean(\|y - ŷ\|) | GPA points | Typical error |
| RMSE | sqrt(mean((y - ŷ)²)) | GPA points | Penalizes large errors |
| R² | 1 - SS_res / SS_tot | unitless | Variance explained |

Why all three:
- MAE is intuitive (GPA points).
- RMSE penalizes outliers.
- R² normalizes against baseline mean.

Day 1 reference (California Housing): R² ≈ 0.5-0.7 for linear models.
Expected here: R² could be negative with N=9 (small sample). Document honestly.

## 8. File Plan
```text
src/ml/
├── __init__.py         PEP 562 lazy imports
├── data.py             load_features, build_feature_matrix
├── split.py            make_loo_cv, make_kfold_cv
├── baseline.py         DummyRegressor wrapper
├── trainer.py          LinearRegression + Ridge wrappers
├── metrics.py          MAE, RMSE, R²
└── pipeline.py         orchestrator (cross-validate all models)
scripts/
└── run_ml_pipeline.py  CLI entry point
tests/
└── test_ml.py          ~15 tests
data/gold/
├── model_metrics.csv
├── model_metrics.json
└── feature_importance.csv
```

## 9. Success Criteria

| # | Criterion | Verification |
|---|---|---|
| 1 | docs/ML_EXPERIMENTS.md exists | this file |
| 2 | src/ml/ package fully implemented | ls src/ml/ |
| 3 | python -m src.ml.data runs cleanly | CLI check |
| 4 | python scripts/run_ml_pipeline.py produces CSV + JSON | manual |
| 5 | All 3 models × 2 CV schemes reported | CSV inspection |
| 6 | ≥15 new tests, all green | pytest tests/test_ml.py -q |
| 7 | Total tests ≥ 214 | pytest tests/ -q |
| 8 | CI still green | GitHub Actions |
| 9 | No leaky features used | test_no_leaky_features |
| 10 | No changes to src/features/, src/warehouse/ | git diff |

## 10. Traceability

| Decision | Curriculum | Guide |
|---|---|---|
| Leakage prevention | Unit 9 (pp. 76-77) | Ch 9 |
| Cross-validation | Applied ML Day 1 | — |
| Ridge regularization | Applied ML Day 1 | — |
| Baseline comparison | Applied ML Day 1 | — |
| Add a layer | — | Ch 12 (Golden Rule 1) |
| Documentation first | Unit 11 | Ch 12 |
| Determinism | Unit 10 (p. 17) | — |

## 11. Risks & Mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | R² negative due to N=9 | Document honestly; compare vs. baseline |
| 2 | Overfitting (LinearRegression) | Show Ridge comparison |
| 3 | Leakage accidentally reintroduced | test_no_leaky_features |
| 4 | Non-deterministic results | REFERENCE_DATE + random_state=42 |
| 5 | Small N → high variance | Report both LOO and KFold |
| 6 | Age drifting over time | Fixed REFERENCE_DATE |

## 12. Version History

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-10-10 | Initial draft |

**Last Updated:** 2026-10-10  
**Status:** 🔵 Planned → In Progress  
**Next Step:** B.2 — src/ml/__init__.py