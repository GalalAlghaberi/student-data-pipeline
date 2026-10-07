# 🏛️ الطبقات المعمارية — Architecture Layers

> **الغرض:** توضيح الفصل بين طبقة التشغيل (OLTP) وطبقة التحليل (OLAP)
> وطبقة التعلم الآلي (ML) في مشروع Student Data Pipeline، تماشيًا مع
> Ch 6 و Ch 7 من دليل "مهارات ومبادئ هندسة البيانات".

---

## 🎯 المبدأ الأساسي

```
OLTP ──── للعمليات اليومية (Insert/Update/Delete)
OLAP ──── للتحليلات والتقارير (Aggregate/Window)
ML   ──── للتدريب والتنبؤ (Features/Model)
```

**قاعدة:** كل طبقة لها:
- **مخطط بيانات مختلف** (3NF vs Star vs Wide)
- **صيغة تخزين مختلفة** (Row vs Column vs Parquet)
- **نمط وصول مختلف** (Point Query vs Scan vs Batch)

---

## 1. الطبقات الثلاث (Three-Layer Model)

### 1.1 — الطبقة التشغيلية (OLTP)

| البُعد | القيمة |
|--------|--------|
| **الاسم** | Operational Layer |
| **الهدف** | تسجيل الأحداث اليومية |
| **المخطط** | 3NF |
| **الصيغة** | SQLite / PostgreSQL (Row-based) |
| **العمليات** | INSERT / UPDATE / DELETE |
| **التقنية** | `src/db_layer.py` |
| **المسار** | `data/raw/university.db` |

**الجداول:**
```
students        — 1 row = 1 student
instructors     — 1 row = 1 instructor
courses         — 1 row = 1 course
enrollments     — 1 row = 1 enrollment (junction)
assessments     — 1 row = 1 assessment
```

**المصدر المنهجي:** Unit 2 + Unit 4

---

### 1.2 — الطبقة التحليلية (OLAP)

| البُعد | القيمة |
|--------|--------|
| **الاسم** | Analytical Layer |
| **الهدف** | تقارير + Aggregations |
| **المخطط** | Star Schema |
| **الصيغة** | Parquet (Column-based) |
| **العمليات** | SELECT + JOIN + GROUP BY |
| **التقنية** | `src/warehouse/star_schema.py` *(مستهدف v4)* |
| **المسار** | `data/gold/*.parquet` |

**الجداول:**
```
fact_student_performance     — 1 row = 1 assessment result
dim_students                 — 1 row = 1 student (denormalized)
dim_courses                  — 1 row = 1 course
dim_instructors              — 1 row = 1 instructor
dim_time                     — 1 row = 1 day/semester
```

**المصدر المنهجي:** Unit 3 + Unit 10  
**المصدر من الدليل:** Ch 6 + Ch 7

---

### 1.3 — طبقة التعلم الآلي (ML-Ready)

| البُعد | القيمة |
|--------|--------|
| **الاسم** | ML Layer |
| **الهدف** | Features + Model Training |
| **المخطط** | Wide Denormalized |
| **الصيغة** | Parquet + NumPy arrays |
| **العمليات** | Train / Predict / Evaluate |
| **التقنية** | `src/features/` + `src/ml/` *(مستهدف v4)* |
| **المسار** | `data/gold/ml_features.parquet` |

**الأعمدة (Feature Set):**
```
student_id                — معرف
attendance_rate           — 0–1
academic_risk_score       — مشتقة
performance_score         — GPA × 25
previous_score_change     — LAG difference
city_rank                 — RANK by city
course_count              — COUNT(DISTINCT)
performance_level         — CASE classification
```

**المصدر المنهجي:** Unit 3 + Unit 6 + Unit 9  
**المصدر من الدليل:** Ch 7 + Ch 8

---

## 2. تدفق البيانات (Data Flow)

```
┌─────────────────────────────────────────────────────────────┐
│                    REAL DATA SOURCES                        │
│  CSV · JSON · API · MongoDB · PostgreSQL · Web              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (Raw)                       │
│  data/bronze/                                               │
│  ├── csv_raw/students_raw.csv                               │
│  ├── api_raw/users.json                                     │
│  └── mongo_raw/students.json                                │
│                                                             │
│  🎯 الهدف: Source of Truth — لا يُعدَّل أبدًا                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │  [ CLEANING + VALIDATION ]
                         │  (Unit 5 + Unit 9)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    SILVER LAYER (Cleaned)                   │
│  data/silver/                                               │
│  ├── csv_clean.csv                                          │
│  ├── sqlite_clean.csv                                       │
│  ├── mongodb_clean.csv                                      │
│  └── ... (5 sources — v3.0.0 output)                        │
│                                                             │
│  🎯 الهدف: بيانات نظيفة موحدة المخطط                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │  [ STAR SCHEMA BUILDER ]
                         │  (Ch 7 من الدليل)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GOLD LAYER (Analytics)                   │
│  data/gold/                                                 │
│  ├── fact_student_performance.parquet                       │
│  ├── dim_students.parquet                                   │
│  ├── dim_courses.parquet                                    │
│  ├── dim_instructors.parquet                                │
│  └── ml_features.parquet                                    │
│                                                             │
│  🎯 الهدف: Analytical + ML-Ready                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │  [ FEATURE ENGINEERING + TRAINING ]
                         │  (ML Day 1)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    ML LAYER (Model)                         │
│  data/gold/                                                 │
│  ├── train_set.parquet                                      │
│  ├── test_set.parquet                                       │
│  └── model_metrics.csv                                      │
│                                                             │
│  🎯 الهدف: نموذج مدرب + مقاييس قابلة للتتبع                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. مقارنة OLTP vs OLAP (Ch 6)

| البُعد | OLTP | OLAP |
|--------|------|------|
| **الهدف** | إدارة العمليات اليومية | الإجابة على أسئلة استراتيجية |
| **نمط التخزين** | Row-based | Column-based |
| **الصيغة** | SQLite / PostgreSQL | Parquet / ORC |
| **العمليات** | INSERT/UPDATE/DELETE | SELECT + Aggregate |
| **الحجم** | آلاف السجلات | ملايين السجلات |
| **الأداء** | كتابة سريعة | قراءة تحليلية سريعة |
| **التطبيع** | 3NF | Star / Denormalized |
| **المكان في المشروع** | `data/raw/university.db` | `data/gold/*.parquet` |

**المرجع:** دليل المبادئ — Ch 6 (OLTP vs OLAP)

---

## 4. مقارنة SQL vs NoSQL vs Files (Ch 4 + Ch 7)

| البُعد | SQL (PostgreSQL) | NoSQL (MongoDB) | Files (Parquet) |
|--------|------------------|-----------------|-----------------|
| **الاستخدام** | بيانات علائقية | مستندات نصف مهيكلة | تحليلات ضخمة |
| **الهيكل** | جداول صارمة | JSON مرن | Columnar |
| **العلاقات** | JOIN سريع | Embedding | Denormalized |
| **التطبيع** | 3NF | Denormalized | Star |
| **الحجم** | GB | GB-TB | TB-PB |
| **المكان في المشروع** | OLTP Layer | Document Store | OLAP Layer |

**المرجع:** دليل المبادئ — Ch 4 (استراتيجيات التخزين)

---

## 5. Grain Definition (Ch 8)

> **القاعدة الذهبية:** قبل أي JOIN، اسأل — *"ماذا يمثل الصف الواحد؟"*

| الجدول | Grain | الطبقة |
|--------|-------|--------|
| `students` | 1 row = 1 student | OLTP |
| `instructors` | 1 row = 1 instructor | OLTP |
| `courses` | 1 row = 1 course | OLTP |
| `enrollments` | 1 row = 1 student-course-semester | OLTP |
| `assessments` | 1 row = 1 assessment | OLTP |
| `fact_student_performance` | 1 row = 1 assessment result | OLAP |
| `dim_students` | 1 row = 1 student | OLAP |
| `ml_features` | 1 row = 1 student | ML |

**⚠️ خطر Row Multiplication:**
عند JOIN `students` ↔ `enrollments` ↔ `assessments`:
- طالب واحد قد يكون له انظمامان و4 تقييمات = 8 صفوف مضاعفة
- **الحل:** فهم Grain قبل كل JOIN

**المرجع:** Unit 3 (صـ 72) + Unit 4 (صـ 59) + دليل المبادئ Ch 8

---

## 6. مصفوفة القرار (Decision Matrix)

### 6.1 — متى نستخدم كل طبقة؟

| السؤال | OLTP | OLAP | ML |
|--------|------|------|-----|
| تسجيل انظمام جديد؟ | ✅ | ❌ | ❌ |
| حساب معدل GPA؟ | ⚠️ | ✅ | ❌ |
| تدريب نموذج؟ | ❌ | ❌ | ✅ |
| JOIN بين 5 جداول؟ | ⚠️ | ✅ | ❌ |
| تحديث تقييم؟ | ✅ | ❌ | ❌ |
| Feature Engineering؟ | ❌ | ⚠️ | ✅ |
| تقرير مدينة؟ | ❌ | ✅ | ❌ |

### 6.2 — قاعدة الدمج

```
إذا كان السؤال "من؟" أو "ماذا؟"       → OLTP
إذا كان السؤال "كم؟" أو "متى؟"        → OLAP
إذا كان السؤال "ماذا سيحدث؟"          → ML
```

---

## 7. المراجع المعمارية

### 7.1 — من المنهج (Course 3)
- **Unit 2:** Relational DB Fundamentals
- **Unit 3:** Advanced SQL (Analytical queries)
- **Unit 4:** Database Design & Normalization (3NF)
- **Unit 6:** Pandas/NumPy/Polars (Performance)
- **Unit 9:** Data Cleaning & Quality
- **Unit 10:** ETL/ELT Pipelines

### 7.2 — من الدليل (مهارات ومبادئ DE)
- **Ch 3:** Architecture First
- **Ch 4:** استراتيجيات التخزين (Parquet/Avro/ORC)
- **Ch 5:** الحوسبة والموارد
- **Ch 6:** OLTP vs OLAP
- **Ch 7:** DW + Fact/Dimension
- **Ch 8:** Grain + Uniqueness
- **Ch 10:** CI/CD + Docker

### 7.3 — مراجع أخرى
- `docs/CURRICULUM_MAP.md` — ربط مفصل
- `ARCHITECTURE.md` — ADR المشروع
- `docs/DATABASE.md` — ERD + Schema

---

## 8. خريطة الطريق التنفيذية

| المرحلة | المخرج | الطبقة |
|---------|--------|--------|
| **v3.0.0** | 5 pipelines + 61 test | OLTP ✅ |
| **v4.0.0 — المرحلة A** | `parquet_writer.py` + `star_schema.py` | OLAP |
| **v4.0.0 — المرحلة B** | `data/bronze|silver|gold/` | تنظيم |
| **v4.0.0 — المرحلة C** | `feature_engineering.py` | ML Features |
| **v4.0.0 — المرحلة D** | `src/ml/*.py` + metrics | ML Model |
| **v4.0.0 — المرحلة E** | CI/CD + Docker + Makefile | Production |

**الجدول الزمني:** ~20 يوم عمل  
**التفاصيل:** راجع `docs/CURRICULUM_MAP.md` — القسم 5

---

## 9. معايير الجودة (Quality Gates)

### 9.1 — قبل الانتقال من OLTP إلى OLAP
- [ ] كل اختبارات `tests/` تمر (61 اختبار)
- [ ] 5 pipelines تنتج 5 ملفات `*_clean.csv`
- [ ] `validate_layer.py` يمر بنجاح

### 9.2 — قبل الانتقال من OLAP إلى ML
- [ ] `fact_student_performance.parquet` موجود
- [ ] حجم Parquet ≤ 30% من CSV المكافئ
- [ ] كل استعلام تحليلي أسرع 10x من CSV

### 9.3 — قبل الانتقال من ML إلى Production
- [ ] Baseline MAE محسوب
- [ ] LinearRegression MAE < Baseline MAE
- [ ] `model_metrics.csv` موثق

---

**آخر تحديث:** 2026-10-07  
**الإصدار المرتبط:** v3.0.0 → v4.0.0  
**المسؤول:** Galal Al-Ghaberi