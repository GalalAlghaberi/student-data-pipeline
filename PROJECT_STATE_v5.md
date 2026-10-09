# Student Data Engineering Pipeline — Context Handoff v4.1.0-dev

## 🎯 معلومات عامة

**المشروع:** Student Data Engineering Pipeline
**المسار:** `C:\Users\Leno\Desktop\progect_python\student_data_pipeline`
**الإصدار الحالي:** `v4.1.0-dev` (Phase A + CI/CD Fixed)
**GitHub:** https://github.com/GalalAlghaberi/student-data-pipeline (Public)
**Python:** 3.14.7 (`C:\PythonLab\python.exe`)
**OS:** Windows 11
**Terminal:** Git Bash (MINGW64)

**قواعد البيانات:** SQLite 3.50.4 + PostgreSQL 18.6 + MongoDB 7.0.14
**أدوات:** PyCharm 2026.2.1 + MongoDB Compass 1.45.1 + pgAdmin 4

---

## 📚 المرجعان المزدوجان

### 1️⃣ المنهج — Course 3 (Data Engineering & Databases for AI)
- ✅ Unit 1: Data Engineering Fundamentals
- ✅ Unit 2: Relational Databases & SQL
- ✅ Unit 3: Advanced SQL
- ✅ Unit 4: Database Design & Normalization
- ✅ Unit 5: Python for Data Engineering
- ✅ **Unit 6: Pandas / NumPy / Polars** (مُكتمل الآن — Phase A)
- ✅ Unit 7: APIs & Web Scraping
- ✅ Unit 8: MongoDB & NoSQL
- ✅ Unit 9: Data Cleaning & Quality
- ✅ Unit 10: ETL/ELT Pipelines
- ✅ Unit 11: Git/GitHub/Documentation

**تغطية المنهج: 100%** ⬆️ (كان 95%)

### 2️⃣ الدليل — مهارات ومبادئ هندسة البيانات (12 فصلًا)
- ✅ Ch 1-4: مفاهيم + بنية + Architecture + Parquet
- ✅ **Ch 5: الحوسبة والموارد** (مُكتمل الآن — Phase A benchmark)
- ✅ Ch 6-9: OLTP/OLAP + DW + نمذجة + جودة
- 🟡 Ch 10: CI/CD + Docker (جزئي — CI ✅, Docker ⏸️)
- ✅ Ch 11: Unit Testing (196 اختبار)
- ✅ Ch 12: المبدأ الجوهري

**تغطية الدليل: ~90%** ⬆️ (كان 72%)

### 🎯 المبدأ الجوهري
> "Facilitating the movement, storage, and access to data in a **repeatable**, **resilient**, and **scalable** manner."
> — دليل مهارات ومبادئ هندسة البيانات (Ch 12)

---

## 📊 حالة Git

### آخر 5 commits
f5b22d3 chore(ci): remove duplicate 'Install dependencies' step
b851beb fix(ci): build offline artifacts before feature tests
bb4e6fd feat(polars): add parallel Polars feature engineer (Phase A)
8198558 docs: add PROJECT_STATE_v5.md — Phase A handoff
2129e95 fix(ci): align workflow with Python 3.13 + markers

### حالة CI (Verified 2026-10-09 04:26 UTC+3)

| Commit | الحالة | المدة |
|---|---|---|
| `f5b22d3` | 🟢 **GREEN** | 35s |
| `b851beb` | 🟢 **GREEN** | 36s |
| `bb4e6fd` | 🔴 RED (قبل الإصلاح) | 35s |
| `8198558` | 🔴 RED (قبل الإصلاح) | 32s |
| `2129e95` | 🟢 GREEN | 34s |

**ملاحظة مهمة:** CI كان أحمر منذ `b6ce32c` حتى `b851beb` (5 commits) دون أن يُلاحظ. السبب: `data/gold/` مستثنى من Git، لكن اختبارات `test_features*.py` تحتاجه.

**Working tree:** نظيف
**Remote:** `git@github.com:GalalAlghaberi/student-data-pipeline.git` (SSH)
**Tags:** `v2.0.0`, `v3.0.0`
**Branch:** `main`

---

## 📁 هيكل المشروع الحالي

student_data_pipeline/
├── pipelines/                          ⭐ 7 Pipelines
│   ├── base_pipeline.py
│   ├── csv_pipeline.py
│   ├── sqlite_pipeline.py
│   ├── postgres_pipeline.py
│   ├── mongodb_pipeline.py
│   ├── json_pipeline.py
│   ├── api_pipeline.py                 # Phase 1 (Unit 7)
│   ├── scraper_pipeline.py             # Phase 1 (Unit 7)
│   ├── run_all_pipelines.py
│   └── compare_pipelines.py
│
├── src/                                # 11 modules + 2 packages
│   ├── config.py
│   ├── logging_setup.py
│   ├── io_layer.py
│   ├── transform_layer.py
│   ├── validate_layer.py
│   ├── storage_layer.py
│   ├── report_layer.py
│   ├── orchestrator.py
│   ├── db_layer.py
│   ├── query_layer.py
│   ├── mongo_layer.py
│   ├── warehouse/                      # Phase 2 (OLAP)
│   │   ├── __init__.py
│   │   ├── parquet_writer.py
│   │   └── star_schema.py
│   └── features/                       # 🆕 Phase A (v4.0.0 + v4.1.0)
│       ├── __init__.py                 # PEP 562 lazy imports
│       ├── engineering.py              # FeatureEngineer (Pandas, 735 lines — FROZEN)
│       ├── engineering_polars.py       # 🆕 PolarsFeatureEngineer (~590 lines)
│       └── synthetic_generator.py      # 🆕 Schema-valid data at scale
│
├── scripts/                            # Utility scripts
│   ├── __init__.py
│   ├── build_university_db.py          # DB builder (من schema.sql + seed.sql)
│   ├── build_mongodb.py
│   ├── check_environment.py
│   ├── export_student_report.py
│   ├── run_sql_file.py
│   └── benchmark_pandas_vs_polars.py   # 🆕 Phase A.5
│
├── data/
│   ├── raw/                            # Bronze Layer
│   │   ├── students_raw.csv            # ✅ tracked
│   │   ├── students_raw.json           # ✅ tracked
│   │   ├── api_students.json           # ✅ tracked
│   │   ├── web_students.html           # ✅ tracked
│   │   └── university.db               # ⚠️ gitignored (regenerable)
│   ├── processed/                      # Silver Layer (gitignored)
│   ├── gold/                           # Gold Layer (gitignored)
│   │   ├── dim_students.parquet (8 rows)
│   │   ├── dim_courses.parquet (5 rows)
│   │   ├── dim_instructors.parquet (4 rows)
│   │   ├── dim_time.parquet (4 rows)
│   │   ├── fact_student_performance.parquet (26 rows)
│   │   ├── fact_enrollment.parquet (13 rows)
│   │   ├── ml_features.parquet         # Pandas (8 × 15)
│   │   ├── ml_features_polars.parquet  # 🆕 Polars (8 × 15)
│   │   ├── train_test_split.parquet
│   │   ├── train_test_split_polars.parquet  # 🆕
│   │   ├── feature_metadata.json
│   │   └── feature_metadata_polars.json     # 🆕
│   ├── synthetic/                      # 🆕 Phase A (gitignored)
│   │   └── students_*.parquet
│   ├── reports/                        # 🆕 Phase A (gitignored)
│   │   └── benchmark_pandas_vs_polars.json
│   └── comparison/
│
├── database/                           # SQL DDL + queries
│   ├── schema.sql
│   ├── seed_data.sql
│   └── queries/
│
├── docs/                               # 10 ملفات توثيق
│   ├── CURRICULUM_MAP.md
│   ├── ARCHITECTURE_LAYERS.md
│   ├── DATA_LINEAGE.md
│   ├── MEDALLION.md
│   ├── FEATURE_STORE.md
│   ├── POLARS_MIGRATION.md             # 🆕 Phase A.1
│   ├── BENCHMARK_RESULTS.md            # 🆕 Phase A.6
│   ├── DATABASE.md
│   ├── POSTGRESQL_SETUP.md
│   └── (MONGODB.md, PIPELINE_ARCHITECTURE.md — Phase C)
│
├── tests/                              # 196 اختبار (+34 من Phase A)
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_io.py (8)
│   ├── test_transform.py (13)
│   ├── test_validate.py (10)
│   ├── test_storage.py (6)
│   ├── test_orchestrator.py (5)
│   ├── test_db_layer.py (10) [db marker]
│   ├── test_query_layer.py (9) [db marker]
│   ├── test_api_pipeline.py (22) [network marker]
│   ├── test_scraper_pipeline.py (31) [network marker]
│   ├── test_warehouse.py (26)
│   ├── test_features.py (22)
│   └── test_features_polars.py         # 🆕 Phase A.4 (34 اختبار)
│
├── .github/workflows/pipeline.yml      # CI: 3.11 + 3.12 + 3.13
├── main.py                             # v2.0.0 (legacy — لا يُلمس)
├── requirements.txt
├── pytest.ini                          # markers: network, db
├── Dockerfile                          # 🟡 غير مُختبَر (Phase D)
├── .gitignore                          # محدَّث (data/synthetic/, data/reports/)
├── README.md
├── ARCHITECTURE.md
├── CHANGELOG.md                        # محدَّث (v4.1.0-dev)
└── HANDOFF_v5.md
✅ ما تم إنجازه في هذه الجلسة
🔷 Phase A — Polars Migration (v4.1.0-dev)
#	الملف	الحجم	الوصف
A.1	docs/POLARS_MIGRATION.md	420 lines	Design + tolerance strategy
A.2	src/features/synthetic_generator.py	254 lines	Schema-valid data at scale
A.3	src/features/engineering_polars.py	764 lines	Parallel PolarsFeatureEngineer
A.4	tests/test_features_polars.py	466 lines	34 اختبار (22 mirror + 12 synthetic)
A.5	scripts/benchmark_pandas_vs_polars.py	361 lines	100K/1M benchmark
A.6	docs/BENCHMARK_RESULTS.md	225 lines	Polars 5-9x speedup
Commit: bb4e6fd (2563 insertions)

🔷 CI/CD Fix (v4.1.0-dev)
Commit	الوصف
b851beb	fix(ci): build offline artifacts (DB → Gold → Features)
f5b22d3	chore(ci): remove duplicate step
🔷 Benchmark Results
N	Pandas	Polars (eager)	Polars (lazy)	Speedup
10K	4.54 ms	0.86 ms	2.64 ms	5.25x
100K	27.73 ms	3.12 ms	8.75 ms	8.88x ⭐
1M	259.82 ms	35.91 ms	52.97 ms	7.23x
ملاحظات:

Polars eager أسرع من lazy في هذا workload (لا filter/pushdown)

Polars 7-9x أسرع — يُثبّت Unit 6 (Scalability Wall)

Peak memory: tracemalloc limitation (Rust allocations غير مرئية)

📈 إحصائيات المشروع
العنصر	v3.0.0	v4.1.0-dev (الآن)
الاختبارات	61	196 (+135)
Pipelines	5	7
مصادر البيانات	5	7
ملفات التوثيق	7	10 (+3)
Layers	2	4 (+ Gold Features + Polars)
Parquet Tables	0	12
CI Status	🔴	🟢
Python Support	3.10-3.12	3.11-3.13
🧪 حالة الاختبارات
bash
python -m pytest tests/ -q
# 196 passed in ~5s

python -m pytest tests/ -q -m "not network and not db"
# 124 passed (CI target)

python -m pytest tests/ -q -m "network"
# 53 passed

python -m pytest tests/ -q -m "db"
# 19 passed
توزيع الاختبارات
الطبقة	الاختبارات	Marker
I/O	8	—
Transform	13	—
Validate	10	—
Storage	6	—
Orchestrator	5	—
Database	10	db
Query	9	db
API Pipeline	22	network
Scraper Pipeline	31	network
Warehouse	26	—
Features (Pandas)	22	—
Features (Polars)	34	—
المجموع	196	—
🎯 المرحلة التالية — الخيارات
⭐ الخيار B (توصية قوية) — Phase B: ML Day 1
داخل المنهج: ML Day 1 (California Housing reference)

الخطوة	المخرج
B.1	docs/ML_EXPERIMENTS.md (توثيق أولًا — القاعدة الذهبية 4)
B.2	src/ml/__init__.py (PEP 562)
B.3	src/ml/split.py (Cross-Validation — N=8 صغير)
B.4	src/ml/baseline.py (DummyRegressor)
B.5	src/ml/trainer.py (LinearRegression + Ridge)
B.6	src/ml/metrics.py (MAE / RMSE / R²)
B.7	tests/test_ml.py (~15 اختبار)
المدة: 4-6 أيام
Target: gpa (regression) مع 6 features
⚠️ ملاحظة: N=8 صفوف صغير — استخدام LeaveOneOut أو KFold بدل Train/Test
مدخلات جاهزة: ml_features.parquet + train_test_split.parquet

الخيار C — Phase C: Documentation Polish
docs/MONGODB.md (Unit 8)

docs/PIPELINE_ARCHITECTURE.md (Unit 10)

تحديث README.md بـ Phase A

تثبيت إصدارات requirements.txt (pip freeze)

المدة: 1-2 أيام

الخيار D — Phase D: Docker + Deployment
دليل Ch 10

تحديث Dockerfile

docker-compose.yml (app + postgres + mongo)

GitHub Actions: Docker build test

المدة: 2-3 أيام

الترتيب الموصى به
text
B (ML)  →  C (Docs)  →  D (Docker)
4-6 يوم    1-2 يوم      2-3 أيام
🛡️ ضمانات عدم التعارض (القواعد الذهبية)
قاعدة 1 — لا تُلغِ طبقة، أضِف طبقة
text
❌ لا تحذف CSV     → ✅ أضف Parquet
❌ لا تترك 3NF     → ✅ أضف Star Schema
❌ لا تلغِ Pandas  → ✅ أضف Polars (Phase A)
❌ لا تلمس main.py → ✅ أضف src/ml/ (Phase B)
قاعدة 2 — كل طبقة في مجلدها
text
src/                ← v3.0.0
src/warehouse/      ← OLAP (Phase 2)
src/features/       ← Feature Engineering (Phase A)
src/ml/             ← ML Layer (Phase B — لاحقًا)
قاعدة 3 — اختبارات v3.0.0 مقدّسة
bash
python -m pytest tests/ -q
# يجب أن يبقى: 140 (كحد أدنى)
# الآن: 196
قاعدة 4 — التوثيق قبل الكود
كل مرحلة تبدأ بملف docs/*.md

Phase A: POLARS_MIGRATION.md ✅

قاعدة 5 — CI يجب أن يبقى أخضر
كل push → 3 jobs × Python versions

يجب التحقق الفعلي من GitHub Actions (ليس افتراض)

§ Lessons Learned — 2026-10-09 Incident
🚨 الحادثة الأولى: CI أحمر صامت (5 commits)
Root Cause:

data/gold/ مستثنى من Git (regenerable)

tests/test_features*.py يحتاج data/gold/

PROJECT_STATE_v5.md ادّعى "CI Green" دون تحقق

فشل صامت لمدة 5 commits (من b6ce32c حتى b851beb)

Fix:

.github/workflows/pipeline.yml: إضافة step "Build offline artifacts"

4 خطوات بناء: DB → Gold → Features (Pandas + Polars)

Lesson:

لا تثق بحالة CI بدون فحص مباشر في المتصفح

CI يُشغّل الفرع كاملًا، ليس الـ commit فقط

🚨 الحادثة الثانية: mv مدمر
ما حدث:

mv data/gold.bak data/gold عندما data/gold موجود

النتيجة: data/gold/gold.bak/* (بنية متداخلة)

نتيجة: 12 ملف أصبحت مدفونة بمستوى إضافي

Fix:

mv data/gold/gold.bak/* data/gold/ ثم rmdir

Lessons:

استخدم cp بدل mv للنسخ الاحتياطي (الأصل يبقى)

تحقق من وجود الهدف قبل النقل:

bash
[ -d "$TARGET" ] && echo "⚠️ exists" || mv "$SRC" "$TARGET"
لا تُخفِ الأخطاء: تجنب 2>/dev/null في العمليات الحرجة

بعد كل عملية: ls -la "$TARGET/" للتأكد

🚨 الحادثة الثالثة: .gitignore سطر مدموج
ما حدث:

text
.duckdb/data/synthetic/    ← سطر واحد مدموج (خاطئ)
بدل:

text
.duckdb/
data/synthetic/            ← سطرين منفصلين
السبب: echo "..." >> بدون \n في نهاية السطر السابق

Fix:

bash
printf '\n# comment\n' >> .gitignore
printf 'data/synthetic/\n' >> .gitignore
Lesson:

استخدم printf مع \n صريحة (لا echo)

تحقق دائمًا: git check-ignore -v <path> يجب أن يُظهر النمط

✅ Pre-commit Checklist (جديد)
قبل أي git commit:

□ python -m pytest tests/ -q → 196 passed
□ python -m pytest tests/ -q -m "not network and not db" → 124 passed
□ CI status من GitHub Actions → 🟢 (verify in browser)
□ git status --short → نظيف (لا .bak أو backup مدفون)
□ git diff --cached --stat → يراجع الملفات
□ لا يوجد data/gold.backup أو data/gold/gold.bak
□ يوجد data/synthetic/ في .gitignore (تحقق: git check-ignore -v data/synthetic/)
أمر فحص سريع:

bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline && \
  pytest tests/ -q | tail -1 && \
  pytest tests/ -q -m "not network and not db" | tail -1 && \
  git status --short && \
  git check-ignore -v data/synthetic/students_1000000.parquet
🖥️ البيئة الحالية
Python Packages
text
pandas 3.0.6         numpy 2.5.3
polars 1.44.2        polars-runtime-32 1.44.2
psycopg2-binary 2.9.13  pytest 9.1.1
pytest-cov 7.1.0     SQLAlchemy 2.0.54
pymongo 4.18.1       requests 2.34.2
beautifulsoup4 4.15.0  tabulate 0.10.0
pyarrow 25.0.1
الخدمات
MongoDB: localhost:27017 — 10 docs ✅

PostgreSQL: localhost:5432 — university_training ✅

SQLite: ملفات محلية ✅

CI/CD
GitHub Actions: .github/workflows/pipeline.yml

Python Matrix: 3.11, 3.12, 3.13

Offline tests per job: 124

Duration: ~35s per job

Latest status: 🟢 Green (verified f5b22d3)

🚀 أوامر التشغيل الأساسية
bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline

# فحص البيئة
python --version
python scripts/check_environment.py

# بناء DB من SQL (offline)
python scripts/build_university_db.py

# بناء Star Schema (OLAP)
python -m src.warehouse.star_schema

# بناء Feature Store (Pandas)
python -m src.features.engineering

# بناء Feature Store (Polars)
python -m src.features.engineering_polars

# Benchmark
python scripts/benchmark_pandas_vs_polars.py --sizes 100000 1000000

# الاختبارات
python -m pytest tests/ -q                                    # 196
python -m pytest tests/ -q -m "not network and not db"       # 124 (CI)
python -m pytest tests/ -q -m "network"                       # 53
python -m pytest tests/ -q -m "db"                            # 19

# Git status
git status
git log --oneline -5
⚠️ ملاحظات مهمة
Git remote: SSH (يعمل بدون كلمة مرور)

PyCharm Env Vars: يجب أن تكون فارغة

Working Directory: جذر المشروع

PostgreSQL password: من PG_PASSWORD env var

MongoDB Service: يعمل تلقائيًا مع Windows

User GitHub: GalalAlghaberi

Terminal: Git Bash مع مسارات /c/Users/...

تحذير LF/CRLF: طبيعي، تجاهله

data/gold/ مستثنى: قابل لإعادة التوليد

data/synthetic/ مستثنى: قابل لإعادة التوليد

data/reports/ مستثنى: قابل لإعادة التوليد

main.py v2.0.0: legacy — لا يُلمس (القاعدة الذهبية 1)

Warnings CI (Node.js 20, Ubuntu 26): طبيعية، لا تؤثر

📋 ما يمكن تحسينه (Technical Debt)
#	المشكلة	الأولوية	المرحلة
1	main.py v2.0.0 قديم	منخفضة	D
2	docs/MONGODB.md مفقود	متوسطة	C
3	docs/PIPELINE_ARCHITECTURE.md مفقود	متوسطة	C
4	actions/*@v4 → Node.js 20 deprecated	منخفضة	C
5	ubuntu-latest → Ubuntu 26 (Oct 2026)	منخفضة	C
6	Scheduled workflow يفشل يوميًا	متوسطة	C
7	matplotlib في البيئة بدون استخدام	منخفضة	—
8	Docker build غير مُختبَر	متوسطة	D
9	pip freeze versions غير مُثبَّتة	منخفضة	C
🎓 حالة ML Day 1 (مرجع)
بدأه المتدرب سابقًا:

Topic: Applied ML Day 1 — California Housing (Regression)

المفاهيم: Train/Test Split، Baseline، LinearRegression، MAE/RMSE/R²

الملفات: Day1_Broken_ML_Challenge_AR.ipynb, Day1_Applied_ML_Student_AR.ipynb

الربط مع المشروع:

✅ ml_features.parquet جاهز (8 صفوف × 15 عمودًا)

✅ train_test_split.parquet جاهز

✅ Data Leakage Prevention مُطبَّق

⚠️ تحذير: N=8 صفوف صغير جدًا → استخدم LeaveOneOut أو KFold بدل Train/Test

Feature Set المقترح:

python
features = [
    "attendance_rate",
    "academic_risk_score",
    "score_change",
    "city_score_gap",
    "n_assessments",
]
target = "gpa"   # للـ Regression
📅 سجل الجلسات
الجلسة الحالية (2026-10-09)
المراحل: Phase A (Polars) + CI/CD Fix
النتيجة:

6 ملفات جديدة (Phase A)

3 commits: bb4e6fd, b851beb, f5b22d3

34 اختبار جديد (196 إجمالي)

CI 🟢 (verified)

2 lessons learned incidents موثقة

الجلسات السابقة
v3.0.0 (2026-10-06): Multi-Source Pipelines (7) + OLAP Layer

v2.0.0 (2026-10-05): Database Design + Normalization

v1.0.0 (2026-10-04): Initial Pipeline


آخر تحديث: 2026-10-09 04:30 UTC+3
المستخدم: Galal Al-Ghaberi
آخر Commit: f5b22d3
الإصدار: v4.1.0-dev
CI Status: 🟢 Verified
المرحلة التالية: B (ML Day 1)