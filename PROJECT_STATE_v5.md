# Student Data Engineering Pipeline — Context Handoff v5.0.0-dev

## 🎯 معلومات عامة

**المشروع:** Student Data Engineering Pipeline
**المسار:** `C:\Users\Leno\Desktop\progect_python\student_data_pipeline`
**الإصدار الحالي:** `v4.0.0-dev` (Phase A + CI/CD Hardened)
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
- ✅ Unit 3: Advanced SQL (Window Functions, CTEs, Ranking, LAG/LEAD)
- ✅ Unit 4: Database Design & Normalization (مطبق في v2.0.0 + Star Schema v3.0.0)
- ✅ Unit 5: Python for Data Engineering
- ✅ Unit 6: Pandas / NumPy / Polars (Polars: مطبق جزئيًا)
- ✅ Unit 7: APIs & Web Scraping — مكتمل في Phase 1
- ✅ Unit 8: MongoDB & NoSQL
- ✅ Unit 9: Data Cleaning & Quality — مطبق في Phase A (Leakage Prevention)
- ✅ Unit 10: ETL/ELT Pipelines
- ✅ Unit 11: Git/GitHub/Documentation

**تغطية المنهج: 100%**

### 2️⃣ الدليل — مهارات ومبادئ هندسة البيانات (12 فصلًا)
- ✅ Ch 1: مفهوم DE + الأهداف
- ✅ Ch 2: بنية المشاريع
- ✅ Ch 3: Architecture First
- ✅ Ch 4: استراتيجيات التخزين — Parquet مطبق (Phase 2 + Phase A)
- ⏳ Ch 5: الحوسبة والموارد — **لم يُطبَّق بعد (Phase B candidate)**
- ✅ Ch 6: OLTP vs OLAP
- ✅ Ch 7: DW + Star Schema — مطبق في Phase 2
- ✅ Ch 8: نمذجة البيانات + Grain — مطبق (explicit grain)
- ✅ Ch 9: جودة البيانات
- 🔄 Ch 10: CI/CD + Docker — GitHub Actions يعمل، Docker جزئيًا
- ✅ Ch 11: Unit Testing — 162 اختبار
- ✅ Ch 12: المبدأ الجوهري

**تغطية الدليل: ~72%**

### 🎯 المبدأ الجوهري
> "Facilitating the movement, storage, and access to data in a **repeatable**, **resilient**, and **scalable** manner."
> — دليل مهارات ومبادئ هندسة البيانات (Ch 12)

---

## 📊 حالة Git

### آخر 8 commits
2129e95 fix(ci): align workflow with Python 3.13 + markers
b6ce32c feat(features): add ML feature store with leakage prevention
b8a1a73 fix(gitignore): use recursive glob for processed outputs
dcf3df6 feat(warehouse): add OLAP layer with Star Schema (Ch 4,7)
4798068 docs: add data lineage tracking (Unit 10,11)
e8eb90f feat(pipelines): add API and scraper pipelines (Unit 7)
1b24306 docs: add curriculum map and architecture layers guide (Phase 0)
a2b0a4c docs: update DATABASE.md (fix ERD + add MongoDB)

text

**Working tree:** نظيف
**Remote:** `git@github.com:GalalAlghaberi/student-data-pipeline.git` (SSH)
**Tags:** `v2.0.0`, `v3.0.0`
**Branch:** `main`
**CI/CD:** 🟢 **Green** (3 Python versions)

---

## 📁 هيكل المشروع الحالي
student_data_pipeline/
├── pipelines/ ⭐ 7 Pipelines
│ ├── base_pipeline.py
│ ├── csv_pipeline.py
│ ├── sqlite_pipeline.py
│ ├── postgres_pipeline.py
│ ├── mongodb_pipeline.py
│ ├── json_pipeline.py
│ ├── api_pipeline.py # Phase 1 (Unit 7)
│ ├── scraper_pipeline.py # Phase 1 (Unit 7)
│ ├── run_all_pipelines.py
│ └── compare_pipelines.py
│
├── src/ # 11 modules + 2 packages
│ ├── config.py
│ ├── logging_setup.py
│ ├── io_layer.py
│ ├── transform_layer.py
│ ├── validate_layer.py
│ ├── storage_layer.py
│ ├── report_layer.py
│ ├── orchestrator.py
│ ├── db_layer.py
│ ├── query_layer.py
│ ├── mongo_layer.py
│ ├── warehouse/ # Phase 2 (OLAP)
│ │ ├── init.py
│ │ ├── parquet_writer.py
│ │ └── star_schema.py
│ └── features/ # 🆕 Phase A
│ ├── init.py # PEP 562 lazy imports
│ └── engineering.py # FeatureEngineer (736 lines)
│
├── data/
│ ├── raw/ # Bronze Layer
│ │ ├── students_raw.csv
│ │ ├── students_raw.json
│ │ ├── university.db
│ │ ├── api_students.json # API cache (offline fallback)
│ │ ├── web_students.html # HTML fixture
│ │ └── student_data.db
│ ├── processed/ # Silver Layer (gitignored)
│ │ ├── csv/csv_clean.csv
│ │ ├── sqlite/sqlite_clean.csv
│ │ ├── postgres/postgres_clean.csv
│ │ ├── mongodb/mongodb_clean.csv
│ │ ├── json/json_clean.csv
│ │ ├── api/api_clean.csv
│ │ └── scraper/scraper_clean.csv
│ ├── gold/ # Gold Layer (gitignored)
│ │ ├── dim_students.parquet (8 rows)
│ │ ├── dim_courses.parquet (5 rows)
│ │ ├── dim_instructors.parquet (4 rows)
│ │ ├── dim_time.parquet (4 rows)
│ │ ├── fact_student_performance.parquet (26 rows)
│ │ ├── fact_enrollment.parquet (13 rows)
│ │ ├── ml_features.parquet # 🆕 Phase A (8 rows × 15 cols)
│ │ ├── train_test_split.parquet # 🆕 Phase A
│ │ └── feature_metadata.json # 🆕 Phase A
│ └── comparison/
│ ├── comparison_report.md
│ └── comparison_data.csv
│
├── database/ # SQL DDL + queries
├── docs/ # 7 ملفات توثيق
│ ├── CURRICULUM_MAP.md
│ ├── ARCHITECTURE_LAYERS.md
│ ├── DATA_LINEAGE.md
│ ├── MEDALLION.md
│ ├── FEATURE_STORE.md # 🆕 Phase A
│ ├── DATABASE.md
│ ├── POSTGRESQL_SETUP.md
│ └── (MONGODB.md, PIPELINE_ARCHITECTURE.md مفقودان — Phase C)
│
├── tests/ # 162 اختبار
│ ├── test_io.py (8)
│ ├── test_transform.py (13)
│ ├── test_validate.py (10)
│ ├── test_storage.py (6)
│ ├── test_orchestrator.py (5)
│ ├── test_db_layer.py (10) [db marker]
│ ├── test_query_layer.py (9) [db marker]
│ ├── test_api_pipeline.py (22) [network marker]
│ ├── test_scraper_pipeline.py (31) [network marker]
│ ├── test_warehouse.py (26)
│ └── test_features.py (22) # 🆕 Phase A
│
├── .github/workflows/pipeline.yml # CI: 3.11 + 3.12 + 3.13
├── main.py # v2.0.0 (legacy — لا يُلمس)
├── requirements.txt # محدَّث (Phase A + CI fix)
├── pytest.ini # markers: network, db
├── Dockerfile
├── .gitignore # محدَّث (recursive glob)
├── README.md # 490 سطر
├── ARCHITECTURE.md
└── CHANGELOG.md # محدَّث (Phase A)

text

---

## ✅ ما تم إنجازه في هذه الجلسة

### 🔷 Phase A — Feature Engineering
**Commits:** `b6ce32c` (Feature) + `b8a1a73` (gitignore fix)

| الملف | الحجم | الوصف |
|---|---|---|
| `src/features/__init__.py` | 20 سطر | PEP 562 lazy imports |
| `src/features/engineering.py` | 736 سطر | `FeatureEngineer` class |
| `tests/test_features.py` | 354 سطر | 22 اختبار |
| `docs/FEATURE_STORE.md` | 199 سطر | Architecture + traceability |

**6 ميزات جديدة:**
| الميزة | الصيغة | المرجع |
|---|---|---|
| `attendance_rate` | `attendance / 100` | Unit 6, p. 37 |
| `academic_risk_score` | `(4 - gpa) + ((100 - attendance) / 25)` | Unit 6, p. 51 |
| `score_change` | `LAG(score) OVER (...)` | Unit 3, pp. 36-38 |
| `city_rank` | `RANK() OVER (PARTITION BY city ...)` (TRAIN only) | Unit 3, p. 33 |
| `city_score_gap` | `avg_score - median(city avg in TRAIN)` | Design |
| `performance_level` | `CASE WHEN avg_score >= 90 ...` | Unit 3, p. 19 |

**🛡️ منع Data Leakage (Unit 9, pp. 76-77):**
- ✅ Split TRAIN/TEST أولًا
- ✅ Statistics من TRAIN فقط
- ✅ `city_rank` من TRAIN peers فقط
- ✅ Idempotent (`random_state=42`)

**نتائج التشغيل:**
- `ml_features.parquet`: 8 صفوف × 15 عمودًا
- `train_test_split`: 6 train + 2 test
- `feature_metadata.json`: catalog + train statistics

### 🔷 CI/CD Hardening
**Commit:** `2129e95`

| الملف | التعديل |
|---|---|
| `.github/workflows/pipeline.yml` | Python matrix 3.11-3.13، `-m "not network and not db"` |
| `requirements.txt` | +6 حزم (numpy, polars, pyarrow, psycopg2, pymongo, SQLAlchemy) |
| `pytest.ini` | markers: `network`, `db` |
| `tests/test_*.py` | `pytestmark` مُطبَّق (4 ملفات) |
| `.gitignore` | recursive glob `**/*.csv` |

**نتائج CI:**
- ✅ Test Pipeline (py3.11) — 34s
- ✅ Test Pipeline (py3.12) — ~30s
- ✅ Test Pipeline (py3.13) — ~30s
- **90 اختبار offline** × 3 إصدارات Python

---

## 📈 إحصائيات المشروع

| العنصر | v3.0.0 | v4.0.0-dev (الآن) |
|---|---|---|
| **الاختبارات** | 61 | **162** (+101) |
| **Pipelines** | 5 | **7** (+2) |
| **مصادر البيانات** | 5 | **7** (+2) |
| **ملفات التوثيق** | 7 | **8** (+1) |
| **Layers** | 2 | **4** (+Gold Features) |
| **Parquet Tables** | 0 | **9** (6 dims/facts + 3 features) |
| **Packages** | 11 modules | +2 (warehouse, features) |
| **CI Status** | 🔴 | 🟢 |
| **Python Support** | 3.10-3.12 | 3.11-3.13 |

---

## 🧪 حالة الاختبارات

```bash
python -m pytest tests/ -q
# 162 passed in ~5s

python -m pytest tests/ -q -m "not network and not db"
# 90 passed (CI target)

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
Features (Phase A)	22	—
المجموع	162	
🎯 المرحلة التالية — الخيارات
الخيار A — Phase B: Polars Migration (توصية)
داخل المنهج (Unit 6)

الخطوة	المخرج	Unit
B.1	src/features/engineering_polars.py	Unit 6
B.2	Lazy pl.scan_parquet()	Unit 6
B.3	Expressions: pl.col().filter()	Unit 6
B.4	tests/test_features_polars.py	Unit 11
B.5	benchmark_pandas_vs_polars.py	Unit 6
B.6	docs/POLARS_MIGRATION.md	Guide Ch 5
المدة: 2-3 أيام
المخرج: مقارنة أداء + src/features/engineering_polars.py

الخيار B — Phase ML: ML Day 1
المرجع: ML Day 1 (California Housing — Regression)

src/ml/split.py (موجود ضمناً في features)

src/ml/baseline.py (DummyRegressor)

src/ml/trainer.py (LinearRegression)

src/ml/metrics.py (MAE, RMSE, R²)

scripts/run_ml_pipeline.py

data/gold/model_metrics.csv

المدة: 4-6 أيام
Target: gpa مع 6 features

الخيار C — Phase C: Documentation Polish
docs/MONGODB.md (Unit 8)

docs/PIPELINE_ARCHITECTURE.md (Unit 10)

تحديث README.md بـ Phase A

Docker build test

Scheduled workflow optimization

المدة: 1-2 أيام

الخيار D — Phase 5: Docker + Deployment
دليل Ch 10 (CI/CD + Docker)

تحديث Dockerfile ليعمل

docker-compose.yml (app + postgres + mongo)

GitHub Actions: Docker build test

المدة: 2-3 أيام

🛡️ ضمانات عدم التعارض (القواعد الذهبية)
قاعدة 1 — لا تُلغِ طبقة، أضِف طبقة
text
❌ لا تحذف CSV     → ✅ أضف Parquet بجانبه
❌ لا تترك 3NF     → ✅ أضف Star Schema فوقه
❌ لا تلغِ SQL     → ✅ أضف Feature Store بجانبه
قاعدة 2 — كل طبقة في مجلدها
text
src/                ← v3.0.0 (يبقى)
src/warehouse/      ← OLAP Layer (Phase 2)
src/features/       ← Feature Engineering (Phase A)
src/ml/             ← ML Layer (Phase B/ML — لاحقًا)
قاعدة 3 — اختبارات v3.0.0 مقدّسة
كل مرحلة تنتهي بـ:

bash
python -m pytest tests/ -q
# يجب أن يبقى: 140 passed (كحد أدنى)
# بعد Phase A: 162 passed
قاعدة 4 — التوثيق قبل الكود
كل مرحلة تبدأ بملف docs/*.md.

قاعدة 5 — CI يجب أن يبقى أخضر
كل push → 3 jobs × Python versions.

🖥️ البيئة الحالية
Python Packages (مُثبتة)
text
pandas 3.0.6         numpy 2.5.3
polars 1.44.2        pymongo 4.18.1
psycopg2-binary 2.9.13  pytest 9.1.1
pytest-cov 7.1.0     SQLAlchemy 2.0.54
requests 2.34.2      beautifulsoup4 4.15.0
tabulate 0.10.0      pyarrow 25.0.1
matplotlib 3.11.2
الخدمات
MongoDB: localhost:27017 — 10 docs ✅

PostgreSQL: localhost:5432 — university_training (8 rows) ✅

SQLite: ملفات محلية ✅

CI/CD
GitHub Actions: .github/workflows/pipeline.yml

Python Matrix: 3.11, 3.12, 3.13

Tests per job: 90 (offline subset)

Duration: ~34s per job

🚀 أوامر التشغيل الأساسية
bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline

# فحص البيئة
python --version
python scripts/check_environment.py

# تشغيل 7 pipelines
python pipelines/run_all_pipelines.py

# بناء Star Schema (OLAP)
python -m src.warehouse.star_schema

# بناء Feature Store (Phase A)
python -m src.features.engineering

# الاختبارات
python -m pytest tests/ -q                    # 162
python -m pytest tests/ -q -m "not network and not db"  # 90 (CI)
python -m pytest tests/ -q -m "network"       # 53
python -m pytest tests/ -q -m "db"            # 19

# Git status
git status
git log --oneline -5
⚠️ ملاحظات مهمة
Git remote: SSH (يعمل بدون كلمة مرور)

PyCharm Env Vars: يجب أن تكون فارغة

Working Directory: جذر المشروع

PostgreSQL password: من PG_PASSWORD env var

MongoDB Service: يعمل تلقائيًا مع Windows

لا تستخدم cat > file << EOF — استخدم PyCharm

User GitHub: GalalAlghaberi

Terminal: Git Bash مع مسارات /c/Users/...

تحذير LF/CRLF: طبيعي، تجاهله

data/gold/ مستثنى: قابل لإعادة التوليد

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

المفاهيم: Train/Test Split، Baseline (DummyRegressor)، LinearRegression، MAE/RMSE/R²

الملفات: Day1_Broken_ML_Challenge_AR.ipynb, Day1_Applied_ML_Student_AR.ipynb

الربط مع المشروع:

✅ ml_features.parquet جاهز

✅ train_test_split.parquet جاهز

✅ Data Leakage Prevention مُطبَّق

🎯 يمكن البدء بـ LinearRegression فورًا

Feature Set المقترح للتدريب:

python
features = [
    "attendance_rate",
    "academic_risk_score",
    "score_change",
    "city_score_gap",
    "n_assessments",
    "gpa",              # (لا — هذا target محتمل)
]
target = "performance_level"  # أو gpa للـ Regression
📅 سجل الجلسات
الجلسة الحالية (2026-10-08/09)
المراحل: Phase A + CI/CD Hardening
النتيجة:

4 commits: b8a1a73, b6ce32c, 2129e95 + docs

22 اختبار جديد (162 إجمالي)

CI يعمل (3 Python versions)

6 features جديدة

Data Leakage Prevention مُطبَّق

الجلسات السابقة
v3.0.0 (2026-10-06): Multi-Source Pipelines (7) + OLAP Layer

v2.0.0 (2026-10-05): Database Design + Normalization

v1.0.0 (2026-10-04): Initial Pipeline (v1)

آخر تحديث: 2026-10-09
المستخدم: Galal Al-Ghaberi
آخر Commit: 2129e95
الإصدار: v4.0.0-dev
المرحلة التالية: A (Polars Migration) — توصية قوية