# Student Data Engineering Pipeline — Context Handoff v4.2.0-dev

## 🎯 معلومات عامة

**المشروع:** Student Data Engineering Pipeline
**المسار:** `C:\Users\Leno\Desktop\progect_python\student_data_pipeline`
**الإصدار الحالي:** `v4.2.0-dev` (Phase A + Phase B Day 1)
**GitHub:** https://github.com/GalalAlghaberi/student-data-pipeline (Public)
**Python:** 3.14.7 (`C:\PythonLab\python.exe`)
**OS:** Windows 11
**Terminal:** Git Bash (MINGW64)

**قواعد البيانات:** SQLite 3.50.4 + PostgreSQL 18.6 + MongoDB 7.0.14
**أدوات:** PyCharm 2026.2.1 + MongoDB Compass 1.45.1 + pgAdmin 4

---

## 📚 المرجعان المزدوجان

### 1️⃣ المنهج — Course 3 (Data Engineering & Databases for AI)
- ✅ Unit 1-5: Fundamentals → Python for DE
- ✅ Unit 6: Pandas / NumPy / Polars (Phase A)
- ✅ Unit 7: APIs & Web Scraping
- ✅ Unit 8: MongoDB & NoSQL
- ✅ Unit 9: Data Cleaning & Quality
- ✅ Unit 10: ETL/ELT Pipelines
- ✅ Unit 11: Git/GitHub/Documentation
- 🟡 Unit 12 (?) — ML Day 1 (Phase B — بدأ)

**تغطية المنهج: 100%**

### 2️⃣ الدليل — مهارات ومبادئ هندسة البيانات (12 فصلًا)
- ✅ Ch 1-4: مفاهيم + بنية + Architecture + Parquet
- ✅ Ch 5: الحوسبة والموارد (Phase A benchmark)
- ✅ Ch 6-9: OLTP/OLAP + DW + نمذجة + جودة
- 🟡 Ch 10: CI/CD + Docker (CI ✅، Docker ⏸️)
- ✅ Ch 11: Unit Testing (221 اختبار)
- ✅ Ch 12: المبدأ الجوهري

**تغطية الدليل: ~90%**

### 🎯 المبدأ الجوهري
> "Facilitating the movement, storage, and access to data in a **repeatable**, **resilient**, and **scalable** manner."
> — دليل مهارات ومبادئ هندسة البيانات (Ch 12)

---

## 📊 حالة Git

### آخر 8 commits
```
c99745e (HEAD -> main, origin/main) fix(requirements): uncomment scikit-learn
5d53f81 docs(ml): add findings §13 — Phase B Day 1 results
44aac38 feat(ml): add test suite + CLI wrapper + R² edge case handling
e5ba030 feat(ml): add baseline (DummyRegressor) + trainer (Linear/Ridge)
3d8ff9f feat(ml): add Phase B data/split/metrics layers + docs
ad1b0c9 docs: add PLAYGROUND.md — data quality exercises
c6c24a1 refactor(db): add defensive FK verification + clearer log
0d116a1 test(features): make split/metadata tests dynamic
```

**Working tree:** نظيف
**Remote:** `git@github.com:GalalAlghaberi/student-data-pipeline.git` (SSH)
**Tags:** `v2.0.0`, `v3.0.0`
**Branch:** `main`

### حالة CI (Verified 2026-10-10)
| Run | Commit | الحالة | المدة |
|---|---|---|---|
| #29 | `c99745e` | 🟢 GREEN | 41s |
| #28 | `5d53f81` | 🔴 RED (قبل fix) | 30s |
| #27 | `ad1b0c9` | 🟢 GREEN | 39s |

---

## 📁 هيكل المشروع الحالي

```
student_data_pipeline/
├── pipelines/                          ⭐ 7 Pipelines
│   ├── base_pipeline.py, csv_pipeline.py
│   ├── sqlite_pipeline.py, postgres_pipeline.py
│   ├── mongodb_pipeline.py, json_pipeline.py
│   ├── api_pipeline.py, scraper_pipeline.py
│   └── run_all_pipelines.py, compare_pipelines.py
│
├── src/                                # 11 modules + 3 packages
│   ├── config.py, logging_setup.py
│   ├── io_layer.py, transform_layer.py, validate_layer.py
│   ├── storage_layer.py, report_layer.py, orchestrator.py
│   ├── db_layer.py                     (defensive FK)
│   ├── query_layer.py, mongo_layer.py
│   ├── warehouse/                      # Phase 2 (OLAP)
│   │   ├── __init__.py
│   │   ├── parquet_writer.py
│   │   └── star_schema.py
│   ├── features/                       # Phase A
│   │   ├── __init__.py                 (PEP 562)
│   │   ├── engineering.py              (Pandas — FROZEN)
│   │   ├── engineering_polars.py       (Polars)
│   │   └── synthetic_generator.py
│   └── ml/                             # ✅ Phase B Day 1
│       ├── __init__.py                 (PEP 562 lazy imports)
│       ├── data.py                     (load + leakage audit)
│       ├── split.py                    (LOO + KFold wrappers)
│       ├── metrics.py                  (MAE/RMSE/R² + NaN handling)
│       ├── baseline.py                 (DummyRegressor)
│       ├── trainer.py                  (Linear + Ridge + registry)
│       └── pipeline.py                 (orchestrator)
│
├── scripts/
│   ├── __init__.py
│   ├── build_university_db.py
│   ├── build_mongodb.py
│   ├── check_environment.py
│   ├── export_student_report.py
│   ├── run_sql_file.py
│   ├── benchmark_pandas_vs_polars.py
│   └── run_ml_pipeline.py              # ✅ Phase B CLI
│
├── data/
│   ├── raw/                            (Bronze، جزئيًا tracked)
│   │   ├── students_raw.csv/json
│   │   ├── api_students.json
│   │   ├── web_students.html
│   │   └── university.db               (gitignored)
│   ├── processed/                      (Silver، gitignored)
│   ├── gold/                           (Gold، gitignored)
│   │   ├── dim_*.parquet (4 files)
│   │   ├── fact_*.parquet (2 files)
│   │   ├── ml_features.parquet         (9 × 16)
│   │   ├── ml_features_polars.parquet
│   │   ├── train_test_split*.parquet
│   │   ├── feature_metadata*.json
│   │   ├── model_metrics.csv           ✅ Phase B (36 rows)
│   │   └── model_metrics.json          ✅ Phase B
│   ├── synthetic/                      (gitignored)
│   ├── reports/                        (gitignored)
│   └── playground/                     (gitignored)
│
├── database/
│   ├── schema.sql, seed_data.sql
│   └── queries/postgresql/
│
├── docs/                               (12 ملفًا)
│   ├── CURRICULUM_MAP.md
│   ├── ARCHITECTURE_LAYERS.md
│   ├── DATA_LINEAGE.md
│   ├── MEDALLION.md
│   ├── FEATURE_STORE.md
│   ├── POLARS_MIGRATION.md             (Phase A)
│   ├── BENCHMARK_RESULTS.md            (Phase A)
│   ├── PLAYGROUND.md
│   ├── ML_EXPERIMENTS.md               ✅ Phase B (326 lines, 13 sections)
│   ├── DATABASE.md
│   ├── POSTGRESQL_SETUP.md
│   └── (MONGODB.md, PIPELINE_ARCHITECTURE.md — Phase C)
│
├── tests/                              # 221 اختبار
│   ├── conftest.py
│   ├── test_io.py (8)
│   ├── test_transform.py (13)
│   ├── test_validate.py (10)
│   ├── test_storage.py (6)
│   ├── test_orchestrator.py (5)
│   ├── test_db_layer.py (13, includes 3 FK)
│   ├── test_query_layer.py (9)
│   ├── test_api_pipeline.py (22)
│   ├── test_scraper_pipeline.py (31)
│   ├── test_warehouse.py (26)
│   ├── test_features.py (22)
│   ├── test_features_polars.py (34)
│   └── test_ml.py (22)                 ✅ Phase B
│
├── .github/workflows/pipeline.yml      # CI: 3.11 + 3.12 + 3.13
├── main.py                             # v2.0.0 (legacy — لا يُلمس)
├── requirements.txt                    # محدَّث (scikit-learn>=1.5 نشط)
├── pytest.ini                          # markers: network, db
├── Dockerfile                          # 🟡 غير مُختبَر (Phase D)
├── .gitignore                          # محدَّث
├── README.md, ARCHITECTURE.md, CHANGELOG.md
├── HANDOFF_v7.md                       ← هذا الـ handoff
└── PROJECT_STATE_v6.md                 ← هذا الملف
```

---

## ✅ ما تم إنجازه

### 🔷 Phase A — Polars Migration (v4.1.0-dev)
| # | الملف | الحجم | الوصف |
|---|---|---|---|
| A.1 | `docs/POLARS_MIGRATION.md` | 420 lines | Design + tolerance strategy |
| A.2 | `src/features/synthetic_generator.py` | 254 lines | Schema-valid data at scale |
| A.3 | `src/features/engineering_polars.py` | 764 lines | Parallel PolarsFeatureEngineer |
| A.4 | `tests/test_features_polars.py` | 466 lines | 34 اختبارًا |
| A.5 | `scripts/benchmark_pandas_vs_polars.py` | 361 lines | 100K/1M benchmark |
| A.6 | `docs/BENCHMARK_RESULTS.md` | 225 lines | Polars 5-9x أسرع |

**Benchmark Results:**
| N | Pandas | Polars (eager) | Speedup |
|---|---|---|---|
| 10K | 4.54 ms | 0.86 ms | 5.25x |
| 100K | 27.73 ms | 3.12 ms | **8.88x** ⭐ |
| 1M | 259.82 ms | 35.91 ms | 7.23x |

### 🔷 Phase B Day 1 — ML Baseline (v4.2.0-dev)

**الملفات المُنجَزة:**
| # | الملف | الحجم | الوصف |
|---|---|---|---|
| B.1 | `docs/ML_EXPERIMENTS.md` | 326 lines | 13 أقسام |
| B.2 | `src/ml/__init__.py` | ~55 lines | PEP 562 |
| B.3 | `src/ml/data.py` | ~190 lines | load + leakage audit |
| B.4 | `src/ml/split.py` | ~110 lines | LOO + KFold(3) |
| B.5 | `src/ml/metrics.py` | ~130 lines | MAE/RMSE/R² + aggregate |
| B.6 | `src/ml/baseline.py` | ~75 lines | DummyRegressor |
| B.7 | `src/ml/trainer.py` | ~130 lines | Linear + Ridge |
| B.8 | `src/ml/pipeline.py` | ~230 lines | orchestrator |
| B.9 | `scripts/run_ml_pipeline.py` | ~70 lines | CLI wrapper |
| B.10 | `tests/test_ml.py` | ~250 lines | 22 اختبارًا |

**Leakage Audit (5 excluded + 6 safe):**
- ❌ `avg_score`, `academic_risk_score`, `performance_level`, `city_score_gap`, `city_rank`
- ✅ Numeric: `attendance_rate`, `n_assessments`, `score_change`, `age`
- ✅ Categorical: `gender`, `city`

**Target:** `gpa` (regression، [0,4])

**النتائج (LOO على N=9):**
| Model | MAE | RMSE | R² |
|---|---|---|---|
| Baseline (mean) | 0.340 | 0.340 | NaN* |
| **LinearRegression** | **0.120** ⭐ | **0.120** | NaN* |
| Ridge(α=1.0) | 0.297 | 0.297 | NaN* |

*R² undefined for LOO (n_test=1) — documented in §7.

**النتائج (KFold(3)):**
| Model | MAE | R² |
|---|---|---|
| baseline | 0.420 | -21.77 |
| linear | 0.423 | -12.42 |
| ridge | 0.535 | -30.51 |

**اكتشاف:** Ridge(α=1.0) أسوأ من Linear على LOO (2.5x) — over-regularization عند N=8.

### 🔷 CI/CD Fix (4 commits)
- `c99745e` — `scikit-learn` كان مُعلَّقًا في requirements → CI فشل
- `5d53f81` — Findings §13 (ملف توثيقي فقط)
- `44aac38` — test suite + CLI + R² edge case
- `e5ba030` — baseline + trainer

---

## 📈 إحصائيات المشروع

| العنصر | v3.0.0 | v4.1.0-dev | **v4.2.0-dev (الآن)** |
|---|---|---|---|
| الاختبارات | 61 | 199 | **221** |
| Pipelines | 5 | 7 | 7 |
| مصادر البيانات | 5 | 7 | 7 |
| ملفات التوثيق | 7 | 10 | **12** |
| Layers | 2 | 4 | **5** (+ ML) |
| Parquet Tables | 0 | 12 | 14 |
| CI Status | 🔴 | 🟢 | 🟢 |
| Python Support | 3.10-3.12 | 3.11-3.13 | 3.11-3.13 |

---

## 🧪 حالة الاختبارات

```bash
python -m pytest tests/ -q
# 221 passed in ~7s

python -m pytest tests/ -q -m "not network and not db"
# 146 passed (CI target)

python -m pytest tests/ -q -m "network"
# 53 passed

python -m pytest tests/ -q -m "db"
# 22 passed
```

### توزيع الاختبارات
| الطبقة | العدد | Marker |
|---|---|---|
| I/O | 8 | — |
| Transform | 13 | — |
| Validate | 10 | — |
| Storage | 6 | — |
| Orchestrator | 5 | — |
| Database | 13 | db |
| Query | 9 | db |
| API Pipeline | 22 | network |
| Scraper Pipeline | 31 | network |
| Warehouse | 26 | — |
| Features (Pandas) | 22 | — |
| Features (Polars) | 34 | — |
| **ML (Phase B)** | **22** | — |
| **المجموع** | **221** | — |

---

## 🎯 المرحلة التالية — الخيارات

### ⭐ الخيار A (توصية قوية) — Phase B Day 2
**داخل المنهج:** ML Day 2 (توسيع baseline)

| الخطوة | المخرج |
|---|---|
| B.2.1 | `docs/ML_EXPERIMENTS_DAY2.md` (توثيق أولًا) |
| B.2.2 | `src/ml/tuning.py` (Ridge α sweep) |
| B.2.3 | `src/ml/importance.py` (feature importance) |
| B.2.4 | `scripts/run_ml_tuning.py` |
| B.2.5 | `tests/test_ml_day2.py` (~10 اختبارات) |
| B.2.6 | `data/gold/ridge_alpha_sweep.csv` |
| B.2.7 | `data/gold/feature_importance.csv` |
| B.2.8 | `data/gold/ablation_results.csv` |

**المدة:** 2-3 أيام
**الهدف:** إيجاد α المثلى + فهم أي feature أكثر تأثيرًا

### الخيار B — Phase C: Documentation Polish
- `docs/MONGODB.md`
- `docs/PIPELINE_ARCHITECTURE.md`
- تحديث `README.md`
- `pip freeze` → pinned versions

**المدة:** 1-2 أيام

### الخيار C — Phase D: Docker + Deploy
- تحديث `Dockerfile`
- `docker-compose.yml`
- GitHub Actions: Docker build test

**المدة:** 2-3 أيام

### الترتيب الموصى به
```
B-D2 (ML Day 2)  →  C (Docs)  →  D (Docker)
  2-3 أيام          1-2 يوم      2-3 أيام
```

---

## 🛡️ ضمانات عدم التعارض (القواعد الذهبية)

### قاعدة 1 — لا تُلغِ طبقة، أضِف طبقة
```
❌ لا تحذف CSV     → ✅ أضف Parquet
❌ لا تترك 3NF     → ✅ أضف Star Schema
❌ لا تلغِ Pandas  → ✅ أضف Polars (Phase A)
❌ لا تلمس main.py → ✅ أضف src/ml/ (Phase B)
```

### قاعدة 2 — كل طبقة في مجلدها
```
src/                ← v3.0.0
src/warehouse/      ← OLAP (Phase 2)
src/features/       ← Feature Engineering (Phase A)
src/ml/             ← ML Layer (Phase B)
```

### قاعدة 3 — اختبارات v3.0.0 مقدّسة
```bash
python -m pytest tests/ -q
# الآن: 221
```

### قاعدة 4 — التوثيق قبل الكود
- كل مرحلة تبدأ بـ `docs/*.md`
- Phase A: `POLARS_MIGRATION.md` ✅
- Phase B: `ML_EXPERIMENTS.md` ✅

### قاعدة 5 — CI يبقى أخضر
- كل push → 3 jobs × Python versions
- **تحقق بصري إلزامي** (حادثة `b6ce32c`)

---

## 🚨 Lessons Learned — 4 Incidents

### 🚨 الحادثة 1: CI أحمر صامت (5 commits)
**Root Cause:** `data/gold/` gitignored + اختبارات تحتاجه → فشل صامت.
**Fix:** إضافة `Build offline artifacts` step في pipeline.yml.
**Lesson:** لا تثق بحالة CI بدون فحص مباشر.

### 🚨 الحادثة 2: `mv` مدمر
**ما حدث:** `mv data/gold.bak data/gold` عندما gold موجود → بنية متداخلة.
**Fix:** `mv data/gold/gold.bak/* data/gold/` ثم `rmdir`.
**Lesson:** استخدم `cp` للنسخ الاحتياطي، تحقق من الهدف قبل النقل.

### 🚨 الحادثة 3: `.gitignore` سطر مدموج
**ما حدث:** `.duckdb/data/synthetic/` مدموج بدل سطرين.
**Fix:** `printf '\n'` بدل `echo`.
**Lesson:** تحقق دائمًا بـ `git check-ignore -v <path>`.

### 🚨 الحادثة 4: scikit-learn مُعلَّق في requirements
**ما حدث:** `# scikit-learn>=1.5` داخل header comment → CI تجاهله.
**Fix:** `c99745e` — نقله إلى قسم خاص بلا `#`.
**Lesson:** `grep -v '^#' requirements.txt | grep <pkg>` قبل commit.

---

## ✅ Pre-commit Checklist

قبل أي `git commit`:

- [ ] `python -m pytest tests/ -q` → **221 passed**
- [ ] `python -m pytest tests/ -q -m "not network and not db"` → **146 passed**
- [ ] CI status من GitHub Actions → 🟢 (verify in browser)
- [ ] `git status --short` → نظيف
- [ ] `git diff --cached --stat` → مراجعة الملفات
- [ ] لا يوجد `data/gold.backup` أو `data/gold/gold.bak`
- [ ] `grep -v '^#' requirements.txt | grep <new-pkg>` → للتأكد من عدم تعليق حزم جديدة
- [ ] `git check-ignore -v data/synthetic/` → يؤكد gitignore

**أمر فحص سريع:**
```bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline && \
  pytest tests/ -q | tail -1 && \
  pytest tests/ -q -m "not network and not db" | tail -1 && \
  git status --short && \
  grep -v '^#' requirements.txt | grep -i scikit
```

---

## 🖥️ البيئة الحالية

### Python Packages
```
pandas 3.0.6         numpy 2.5.3
polars 1.44.2        polars-runtime-32 1.44.2
scikit-learn 1.9.1   ← 🆕 Phase B
psycopg2-binary 2.9.13  pytest 9.1.1
pytest-cov 7.1.0     SQLAlchemy 2.0.54
pymongo 4.18.1       requests 2.34.2
beautifulsoup4 4.15.0  tabulate 0.10.0
pyarrow 25.0.1
```

### الخدمات
- MongoDB: `localhost:27017` — 10 docs ✅
- PostgreSQL: `localhost:5432` — `university_training` ✅
- SQLite: ملفات محلية ✅

### CI/CD
- GitHub Actions: `.github/workflows/pipeline.yml`
- Python Matrix: 3.11, 3.12, 3.13
- Offline tests per job: **146**
- Duration: ~41s per job
- Latest status: 🟢 Green (Run #29 on c99745e)

---

## 🚀 أوامر التشغيل الأساسية

```bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline

# فحص البيئة
python --version
python scripts/check_environment.py

# بناء DB من SQL
python scripts/build_university_db.py

# بناء Star Schema
python -m src.warehouse.star_schema

# بناء Feature Store
python -m src.features.engineering            # Pandas
python -m src.features.engineering_polars     # Polars

# Phase B — ML Pipeline
python -m src.ml.data
python -m src.ml.split
python -m src.ml.metrics
python -m src.ml.baseline
python -m src.ml.trainer
python -m src.ml.pipeline
python scripts/run_ml_pipeline.py

# الاختبارات
python -m pytest tests/ -q                                  # 221
python -m pytest tests/ -q -m "not network and not db"     # 146
python -m pytest tests/ -q -m "db"                          # 22
python -m pytest tests/ -q -m "network"                     # 53
python -m pytest tests/test_ml.py -v                        # 22

# Git
git status
git log --oneline -10
```

---

## ⚠️ ملاحظات مهمة

1. **Git remote:** SSH (يعمل بدون كلمة مرور)
2. **PyCharm Env Vars:** فارغة
3. **PostgreSQL password:** من `PG_PASSWORD` env var
4. **MongoDB Service:** يعمل تلقائيًا
5. **User GitHub:** `GalalAlghaberi`
6. **تحذير LF/CRLF:** طبيعي، تجاهله
7. **`data/gold/`:** مستثنى، قابل لإعادة التوليد
8. **`data/synthetic/`:** مستثنى
9. **`data/reports/`:** مستثنى
10. **`main.py v2.0.0`:** legacy — لا يُلمس
11. **`REFERENCE_DATE = 2026-10-10`** (في `src/ml/data.py`): **ثابت — لا تُغيّره**
12. **R² على LOO = NaN:** طبيعي (n=1)، مُعالَج — لا تحاول "إصلاحه"

---

## 📋 ما يمكن تحسينه (Technical Debt)

| # | المشكلة | الأولوية | المرحلة |
|---|---|---|---|
| 1 | `main.py v2.0.0` قديم | منخفضة | D |
| 2 | `docs/MONGODB.md` مفقود | متوسطة | C |
| 3 | `docs/PIPELINE_ARCHITECTURE.md` مفقود | متوسطة | C |
| 4 | `actions/*@v4` → Node.js 20 deprecated | منخفضة | C |
| 5 | `ubuntu-latest` → Ubuntu 26 (Oct 2026) | منخفضة | C |
| 6 | Scheduled workflow يفشل يوميًا | متوسطة | C |
| 7 | `matplotlib` في البيئة بدون استخدام | منخفضة | — |
| 8 | Docker build غير مُختبَر | متوسطة | D |
| 9 | `pip freeze` versions غير مُثبَّتة | منخفضة | C |
| 10 | **Ridge α=1.0 قد يكون غير مثالي** | عالية | **Day 2** |
| 11 | **Feature importance غير مُستخرَجة** | عالية | **Day 2** |

---

## 🎓 حالة ML Day 1 + Day 2 Preview

### Day 1 (مكتمل)
- ✅ Leakage audit (5 excluded, 6 safe)
- ✅ CV strategy (LOO + KFold(3))
- ✅ 3 models (baseline/linear/ridge)
- ✅ MAE/RMSE/R²
- ✅ **النتيجة:** Linear (MAE=0.120) > Ridge(0.297) > Baseline(0.340)

### Day 2 (التالي)
- α sweep: {0.001, 0.01, 0.1, 1.0, 10.0, 100.0}
- Feature importance
- Ablation: numeric only vs numeric+categorical
- Interaction features

---

## 📅 سجل الجلسات

### الجلسة الحالية (2026-10-10)
**المراحل:** Phase B Day 1 (ML Baseline) + CI Fix #4
**النتيجة:**
- 10 ملفات جديدة (Phase B)
- 5 commits: `3d8ff9f`, `e5ba030`, `44aac38`, `5d53f81`, `c99745e`
- 22 اختبار جديد (199 → 221)
- CI 🟢 (Run #29)
- حادثة رابعة موثّقة (requirements comment)

### الجلسات السابقة
- v4.1.0-dev (2026-10-09): Phase A (Polars) + CI/CD Fix
- v3.0.0 (2026-10-06): Multi-Source Pipelines (7) + OLAP Layer
- v2.0.0 (2026-10-05): Database Design + Normalization
- v1.0.0 (2026-10-04): Initial Pipeline

---

**آخر تحديث:** 2026-10-10 04:35 UTC+3
**المستخدم:** Galal Al-Ghaberi
**آخر Commit:** `c99745e`
**الإصدار:** v4.2.0-dev
**CI Status:** 🟢 Verified (Run #29)
**المرحلة التالية:** Phase B Day 2 (α sweep + feature importance)