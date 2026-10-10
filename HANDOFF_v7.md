Markdown
# تقرير شامل — حالة المشروع للانتقال إلى محادثة جديدة

**التاريخ:** 2026-10-10  
**الإصدار:** v4.2.0-dev (Phase B Day 1 مكتملة)  
**آخر commit:** c99745e  
**الرابط السابق:** (المحادثة الحالية)  

---

## 🎯 تعليمات البدء السريع للمحادثة الجديدة

### الملفات التي يجب إرسالها في الرسالة الأولى:
1. `PROJECT_STATE_v6.md` (الجذر ~700 سطر)
2. `HANDOFF_v7.md` (الجذر ~700 سطر) ← هذا الملف
3. `.github/workflows/pipeline.yml` (45 سطر)
4. `docs/PLAYGROUND.md` (81 سطر)
5. `docs/POLARS_MIGRATION.md` (420 سطر)
6. `docs/BENCHMARK_RESULTS.md` (225 سطر)
7. `docs/ML_EXPERIMENTS.md` (326 سطر) ← **جديد — مهم**

### القالب الجاهز للإرسال:
```text
- استئناف مشروع Student Data Engineering Pipeline
- الحالة: آخر commit: c99745e
- الاختبارات: 221 passed (offline 146)
- CI: 🟢 Green (Python 3.11, 3.12, 3.13)
- Phase A: ✅ مكتملة (Polars Migration)
- Phase B Day 1: ✅ مكتملة (ML baseline)
- Phase B Day 2: ⏳ جاهز للبدء من الصفر
- المطلوب: اقرأ HANDOFF_v7.md أولًا
- أكّد الفهم
- ابدأ Phase B Day 2: docs/ML_EXPERIMENTS_DAY2.md
- الملفات المرفقة (7 ملفات): PROJECT_STATE_v6.md, HANDOFF_v7.md, pipeline.yml, PLAYGROUND.md, POLARS_MIGRATION.md, BENCHMARK_RESULTS.md, ML_EXPERIMENTS.md
- البيئة: Windows 11 + Git Bash
- Python 3.14.7 (C:\PythonLab\python.exe)
- المسار: C:\Users\Leno\Desktop\progect_python\student_data_pipeline
- SSH: git@github.com:GalalAlghaberi/student-data-pipeline.git
هل أنت جاهز لاستلام الملفات وتأكيد الفهم؟
📊 القسم 1: الحالة الحالية
Git Log (آخر 8 commits)
Plaintext
c99745e (HEAD -> main, origin/main) fix(requirements): uncomment scikit-learn
5d53f81 docs(ml): add findings §13 — Phase B Day 1 results
44aac38 feat(ml): add test suite + CLI wrapper + R² edge case handling
e5ba030 feat(ml): add baseline (DummyRegressor) + trainer (Linear/Ridge)
3d8ff9f feat(ml): add Phase B data/split/metrics layers + docs
ad1b0c9 docs: add PLAYGROUND.md — data quality exercises
c6c24a1 refactor(db): add defensive FK verification + clearer log
0d116a1 test(features): make split/metadata tests dynamic
$ git status --short — clean (working tree نظيف)

Tags: v2.0.0, v3.0.0

الاختبارات
الفئة	العدد	Marker / الوصف
Offline (CI target)	146	not network and not db
DB	22	db
Network	53	network
Full Suite	221	جميع الاختبارات خضراء
CI/CD
الحالة: 🟢 Green (Run #29 على c99745e)

Matrix: Python 3.11, 3.12, 3.13

المدة: ~41 ثانية/job

Workflow: .github/workflows/pipeline.yml

Build steps: DB → Gold → Features (Pandas + Polars) → Tests

✅ القسم 2: ما تم إنجازه في هذه الجلسة
Phase B Day 1 — ML Baseline (v4.2.0-dev)
#	الملف	الحجم	الوصف
B.1	docs/ML_EXPERIMENTS.md	326 سطرًا	13 قسمًا (Objective → Findings)
B.2	src/ml/__init__.py	~55 سطرًا	PEP 562 lazy imports
B.3	src/ml/data.py	~190 سطرًا	load_features + build_feature_matrix
B.4	src/ml/split.py	~110 سطرًا	LeaveOneOut + KFold(3)
B.5	src/ml/metrics.py	~130 سطرًا	MAE/RMSE/R² + aggregate
B.6	src/ml/baseline.py	~75 سطرًا	DummyRegressor
B.7	src/ml/trainer.py	~130 سطرًا	LinearRegression + Ridge(α=1.0)
B.8	src/ml/pipeline.py	~230 سطرًا	orchestrator
B.9	scripts/run_ml_pipeline.py	~70 سطرًا	CLI wrapper
B.10	tests/test_ml.py	~250 سطرًا	22 اختبارًا
النتائج العلمية (موثّقة في ML_EXPERIMENTS.md §13)
LOO (LeaveOneOut) — N=9:

Baseline (mean): MAE = 0.340, RMSE = 0.340, R² = NaN*

LinearRegression: MAE = 0.120 ⭐, RMSE = 0.120, R² = NaN*

Ridge(α=1.0): MAE = 0.297, RMSE = 0.297, R² = NaN*

(R² undefined on LOO folds (n_test=1) → NaN + n_valid=0)

KFold(3):

Baseline: MAE = 0.420, R² = -21.773

Linear: MAE = 0.423, R² = -12.423

Ridge: MAE = 0.535, R² = -30.513

اكتشاف مثير: Ridge(α=1.0) أسوأ من LinearRegression على LOO بفارق 2.5x (over-regularization مع N=8).

Leakage Audit (مُراجَع رياضيًا)
5 أعمدة مستبعدة:

avg_score — gpa = avg_score / 25

academic_risk_score — يستخدم gpa مباشرة

performance_level — مشتق من avg_score

city_score_gap — محسوب من avg_score

city_rank — مرتب بـ avg_score

6 features آمنة:

Numeric: attendance_rate, n_assessments, score_change, age

Categorical: gender, city

CI/CD Fix (حادثة رابعة)
c99745e — # scikit-learn>=1.5 كان داخل تعليق في requirements.txt → CI تجاهله → test_ml.py فشل بـ ModuleNotFoundError. الحل: نقله خارج التعليق.

⏳ القسم 3: ما لم يبدأ بعد
Phase B Day 2 (⏸️ التالي مباشرة)
α sweep: {0.01, 0.1, 1.0, 10.0} لـ Ridge

Feature interactions (مثل attendance_rate × n_assessments)

data/gold/feature_importance.csv (معاملات Linear)

مقارنة مع/بدون categorical features

docs/ML_EXPERIMENTS_DAY2.md (توثيق أولًا — القاعدة الذهبية 4)

Phase C — Docs Polish (⏸️ مؤجّل)
docs/MONGODB.md

docs/PIPELINE_ARCHITECTURE.md

تثبيت إصدارات requirements.txt (pip freeze)

Phase D — Docker + Deploy (⏸️ مؤجّل)
Dockerfile (موجود، غير مُختبَر)

docker-compose.yml

GitHub Actions: Docker build test

🎯 القسم 4: تصميم Phase B Day 2 (الخطوة التالية)
الأهداف
α Sweep: إثبات أن α=1.0 كبير جدًا → إيجاد القيمة المثلى

Feature Importance: استخراج معاملات LinearRegression (بعد encoding)

Ablation: قياس تأثير كل مجموعة features

Feature Interactions: إضافة تفاعلات بسيطة

الملفات المُخطَّطة
Plaintext
docs/ML_EXPERIMENTS_DAY2.md       (توثيق أولًا)
src/ml/tuning.py                  (α sweep)
src/ml/importance.py              (feature importance)
scripts/run_ml_tuning.py          (CLI)
tests/test_ml_day2.py             (~10 اختبار)
data/gold/
├── ridge_alpha_sweep.csv
├── feature_importance.csv
└── ablation_results.csv
التجارب
Ridge α sweep: LOO MAE لكل α ∈ {0.001, 0.01, 0.1, 1.0, 10.0, 100.0}

Feature importance: استخراج model.coef_ من LinearRegression

Ablation: {numeric only} vs {numeric + categorical} vs {all}

Interaction: attendance_rate × score_change

📁 القسم 5: هيكل المشروع (محدَّث)
Plaintext
student_data_pipeline/
├── pipelines/                  7 Pipelines
├── src/
│   ├── config.py, logging_setup.py, io_layer.py, ...
│   ├── db_layer.py             (defensive FK)
│   ├── warehouse/              (Star Schema)
│   ├── features/               (Phase A)
│   │   ├── engineering.py          (Pandas — FROZEN)
│   │   ├── engineering_polars.py   (Polars)
│   │   └── synthetic_generator.py
│   └── ml/                     ✅ Phase B Day 1
│       ├── __init__.py             (PEP 562)
│       ├── data.py                 (load + leakage audit)
│       ├── split.py                (LOO + KFold)
│       ├── metrics.py              (MAE/RMSE/R² + NaN handling)
│       ├── baseline.py             (DummyRegressor)
│       ├── trainer.py              (Linear + Ridge)
│       └── pipeline.py             (orchestrator)
├── data/
│   ├── raw/                    (Bronze)
│   ├── processed/              (Silver، gitignored)
│   ├── gold/                   (Gold، gitignored)
│   │   ├── ml_features.parquet          (9 × 16)
│   │   ├── model_metrics.csv            ← 🆕 Phase B
│   │   └── model_metrics.json           ← 🆕 Phase B
│   ├── synthetic/              (gitignored)
│   ├── reports/                (gitignored)
│   └── playground/             (gitignored)
├── database/                   (SQL DDL)
├── docs/                       (12 ملفًا)
│   ├── CURRICULUM_MAP.md
│   ├── ARCHITECTURE_LAYERS.md
│   ├── DATA_LINEAGE.md
│   ├── MEDALLION.md
│   ├── FEATURE_STORE.md
│   ├── POLARS_MIGRATION.md
│   ├── BENCHMARK_RESULTS.md
│   ├── PLAYGROUND.md
│   ├── ML_EXPERIMENTS.md       ← 🆕 Phase B
│   ├── DATABASE.md
│   └── POSTGRESQL_SETUP.md
├── tests/                      (221 اختبار)
│   ├── test_io.py (8), test_transform.py (13)
│   ├── test_validate.py (10), test_storage.py (6)
│   ├── test_orchestrator.py (5), test_db_layer.py (13)
│   ├── test_query_layer.py (9), test_api_pipeline.py (22)
│   ├── test_scraper_pipeline.py (31), test_warehouse.py (26)
│   ├── test_features.py (22), test_features_polars.py (34)
│   └── test_ml.py (22)         ← 🆕 Phase B
├── scripts/
│   ├── build_university_db.py, build_mongodb.py
│   ├── check_environment.py, benchmark_pandas_vs_polars.py
│   └── run_ml_pipeline.py      ← 🆕 Phase B
├── .github/workflows/pipeline.yml
├── main.py                     (v2.0.0، لا يُلمس)
├── requirements.txt            (محدَّث — scikit-learn>=1.5 نشط)
├── pytest.ini, Dockerfile, .gitignore
├── README.md, ARCHITECTURE.md, CHANGELOG.md
├── HANDOFF_v7.md               ← هذا الملف
└── PROJECT_STATE_v6.md
🛡️ القسم 6: القواعد الذهبية (يجب احترامها)
لا تُلغِ طبقة، أضِف طبقة:

❌ لا تحذف CSV ⟶ ✅ أضف Parquet بجانبه

❌ لا تلغِ Pandas ⟶ ✅ أضف Polars (Phase A)

❌ لا تلمس main.py ⟶ ✅ أضف src/ml/ (Phase B)

كل طبقة في مجلدها: src/, src/warehouse/, src/features/, src/ml/.

اختبارات v3.0.0 مقدّسة: pytest tests/ -q ⟶ 221 كحد أدنى.

التوثيق قبل الكود: كل مرحلة تبدأ بملف docs/*.md.

CI يبقى أخضر: كل push يختبر 3 إصدارات Python مع تحقق فعلي.

Pre-commit Checklist:

□ pytest tests/ -q = 221

□ pytest -m "not network and not db" = 146

□ CI status من GitHub Actions ⟶ 🟢 (تحقق بصري)

□ git status --short نظيف

□ grep -v '^#' requirements.txt | grep -i <new-pkg> ← تأكد أن الحزمة غير مُعلَّقة

🖥️ القسم 7: البيئة
Python: 3.14.7 (C:\PythonLab\python.exe)

Packages الرئيسية:

pandas 3.0.6, numpy 2.5.3, polars 1.44.2

scikit-learn 1.9.1 ← 🆕 مُستخدم في Phase B

psycopg2-binary 2.9.13, pytest 9.1.1, pytest-cov 7.1.0

SQLAlchemy 2.0.54, pymongo 4.18.1, requests 2.34.2, beautifulsoup4 4.15.0, tabulate 0.10.0, pyarrow 25.0.1

الخدمات:

MongoDB: localhost:27017

PostgreSQL: localhost:5432 (university_training)

SQLite: ملفات محلية

البيئة العامة: Windows 11 | Git Bash (MINGW64) | PyCharm 2026.2.1 | GitHub: GalalAlghaberi

🚀 القسم 8: الأوامر الأساسية
Bash
cd /c/Users/Leno/Desktop/progect_python/student_data_pipeline

# ═══ فحص البيئة ═══
python --version
python scripts/check_environment.py

# ═══ بناء Pipeline كامل من الصفر ═══
python scripts/build_university_db.py         # 1. DB
python -m src.warehouse.star_schema           # 2. Gold Layer
python -m src.features.engineering            # 3. Features (Pandas)
python -m src.features.engineering_polars     # 4. Features (Polars)

# ═══ Phase B — ML Pipeline ═══
python -m src.ml.data                          # 1. Sanity (leakage-safe matrix)
python -m src.ml.split                         # 2. Sanity (LOO + KFold)
python -m src.ml.metrics                       # 3. Sanity (MAE/RMSE/R²)
python -m src.ml.baseline                      # 4. Sanity (Dummy)
python -m src.ml.trainer                       # 5. Sanity (Linear + Ridge)
python -m src.ml.pipeline                      # 6. Full pipeline (36 rows)
python scripts/run_ml_pipeline.py              # 7. CLI wrapper

# ═══ الاختبارات ═══
python -m pytest tests/ -q                                  # 221
python -m pytest tests/ -q -m "not network and not db"     # 146 (CI)
python -m pytest tests/ -q -m "db"                          # 22
python -m pytest tests/ -q -m "network"                     # 53
python -m pytest tests/test_ml.py -v                        # 22 (Phase B)

# ═══ Git ═══
git status
git log --oneline -10

# ═══ خدمات ═══
pg_isready -h localhost -p 5432
mongosh --eval "db.adminCommand('ping')" --quiet
⚠️ القسم 9: ملاحظات حرجة
data/gold/ gitignored: قابل لإعادة التوليد بالأوامر أعلاه.

REFERENCE_DATE = 2026-10-10: ثابت في src/ml/data.py لضمان idempotency. لا تُغيّره.

R² على LOO = NaN: طبيعي — n_test=1 → SS_tot=0. مُعالَج في metrics.r2(). لا تحاول "إصلاحه".

Ridge(α=1.0) أسوأ من Linear على LOO: موثّق، لم يُضبَط (Day 1 policy). Day 2 سيفحص α sweep.

requirements.txt: تحقّق دائمًا بـ grep -v '^#' requirements.txt | grep <pkg> — لا حزم مُعلَّقة.

SQLite FK: استخدم db_layer.connect() دائمًا.

Pre-commit safety: cp بدل mv، تحقّق من المسارات، لا 2>/dev/null على العمليات الحرجة.

PyCharm: استخدم Ctrl+H للاستبدال الشامل — لكن راجع التغييرات قبل القبول.

🎯 القسم 10: الخطوة التالية المقترحة
الأولوية 1 (مُوصى): Phase B Day 2 — α sweep + feature importance (2-3 أيام)

ابدأ بـ docs/ML_EXPERIMENTS_DAY2.md (التوثيق أولًا)

ثم src/ml/tuning.py + src/ml/importance.py

الهدف: إيجاد α المثلى + فهم أي feature أكثر تأثيرًا

الأولوية 2: Phase C (Docs Polish) — 1-2 أيام.

الأولوية 3: Phase D (Docker) — 2-3 أيام.

📋 القسم 11: قائمة التحقق النهائية قبل الانتقال
[ ] git status --short نظيف

[ ] git log --oneline -3 يُظهر c99745e

[ ] pytest tests/ -q = 221 passed

[ ] pytest -m "not network and not db" = 146 passed

[ ] CI 🟢 على GitHub Actions (Run #29)

[ ] PROJECT_STATE_v6.md موجود

[ ] HANDOFF_v7.md موجود ← هذا الملف

[ ] docs/ML_EXPERIMENTS.md موجود (326 سطرًا)

[ ] src/ml/ مكتمل (7 ملفات)

[ ] tests/test_ml.py موجود (22 اختبارًا)

[ ] requirements.txt — scikit-learn>=1.5 نشط (بلا #)

📚 القسم 12: ملخص إنجازات الجلسة
Phase B Day 1 (ML Baseline):
7 ملفات في src/ml/ (~920 سطرًا)

1 ملف CLI في scripts/ (~70 سطرًا)

1 ملف اختبار (~250 سطرًا، 22 اختبارًا)

1 ملف توثيق (326 سطرًا، 13 قسمًا)

5 commits جديدة

+22 اختبار (199 → 221)

CI Fix: حادثة رابعة (التعليق الخفي في requirements)

النتيجة العلمية الأبرز:
LinearRegression (MAE=0.120) يتفوّق على Ridge(α=1.0) (MAE=0.297) بـ 2.5x على LOO — دليل على over-regularization عند N=9.

المشروع الآن جاهز 100% لبدء Phase B Day 2 في المحادثة الجديدة.