# 🗺️ خريطة المنهج — Curriculum Map

> **الغرض:** توثيق العلاقة بين وحدات Course 3 (Units 1–11) وفصول
> دليل "مهارات ومبادئ هندسة البيانات" (Ch 1–12)، لضمان عدم التعارض
> بين "ماذا نتعلم" (المنهج) و "كيف نبني باحتراف" (الدليل).

---

## 🎯 الفلسفة الموحّدة

```
المنهج (Units)    = ماذا نتعلم       → تغطية معرفية
الدليل (Chapters) = كيف نبني باحتراف → تطبيق هندسي
المشروع           = نقطة الالتقاء    → كلاهما يخدمان ML-Ready Data
```

**الخلاصة:** لا يوجد تعارض — توجد طبقات تكامل.

---

## 1. مصفوفة الربط الشاملة

### 1.1 — وحدات المنهج (Course 3)

| Unit | الموضوع | المخرج الفعلي في المشروع | الحالة |
|------|---------|--------------------------|--------|
| **1** | Data Engineering Fundamentals | `main.py` + `src/orchestrator.py` | ✅ v1 |
| **2** | Relational DB & SQL | `src/db_layer.py` + `database/schema.sql` | ✅ v1 |
| **3** | Advanced SQL | `database/queries/advanced/` + `postgresql/` | ✅ v2 |
| **4** | Database Design & Normalization | 5 جداول 3NF + ERD في `DATABASE.md` | ✅ v2 |
| **5** | Python for Data Engineering | 11 module في `src/` + 61 اختبار | ✅ v1–v3 |
| **6** | Pandas / NumPy / Polars | `src/transform_layer.py` | ✅ v1 |
| **7** | APIs & Web Scraping | `pipelines/api_pipeline.py` *(قيد الإنشاء)* | 🔄 v4 |
| **8** | MongoDB & NoSQL | `src/mongo_layer.py` + `pipelines/mongodb_pipeline.py` | ✅ v3 |
| **9** | Data Cleaning & Quality | `src/validate_layer.py` + `data/comparison/` | ✅ v2 |
| **10** | ETL/ELT Pipelines | `pipelines/run_all_pipelines.py` (5 مصادر) | ✅ v3 |
| **11** | Git / GitHub / Docs | v3.0.0 + 7 ملفات توثيق | ✅ v3 |

### 1.2 — فصول الدليل (Guide)

| Ch | الموضوع | المخرج الفعلي / المستهدف | الحالة |
|----|---------|--------------------------|--------|
| **1** | مفهوم DE + الأهداف | `README.md` قسم Overview | ✅ |
| **2** | بنية المشاريع | مجلدات `src/ pipelines/ tests/ docs/` | ✅ |
| **3** | Architecture First | `ARCHITECTURE.md` (561 سطر) | ✅ v2 |
| **4** | استراتيجيات التخزين | `src/warehouse/parquet_writer.py` *(مستهدف v4)* | ⏳ |
| **5** | الحوسبة والموارد | `scripts/benchmark.py` *(مستهدف v4)* | ⏳ |
| **6** | OLTP vs OLAP | `docs/ARCHITECTURE_LAYERS.md` | ✅ v4 |
| **7** | DW + Star Schema | `src/warehouse/star_schema.py` *(مستهدف v4)* | ⏳ |
| **8** | نمذجة البيانات + Grain | `DATABASE.md` قسم Grain | ✅ v2 |
| **9** | جودة البيانات | `src/validate_layer.py` + QUARANTINE | ✅ v2 |
| **10** | CI/CD + Docker | `.github/workflows/` + `Dockerfile` | ✅ v3 |
| **11** | Unit Testing | `tests/` (61 اختبار) | ✅ v3 |
| **12** | المبدأ الجوهري | موثّق في `README.md` | ✅ |

---

## 2. خريطة التكامل (Integration Map)

### 2.1 — كيف يخدم كل Unit فصول الدليل؟

| Unit | يخدم Chapters | العلاقة |
|------|---------------|---------|
| Unit 1 | Ch 1, 3, 12 | يبني الأساس المفاهيمي |
| Unit 2 | Ch 6, 8 | OLTP + Grain |
| Unit 3 | Ch 6, 8 | Analytical SQL في OLAP |
| Unit 4 | Ch 7, 8 | 3NF أساس Star Schema |
| Unit 5 | Ch 3, 11 | Programming Layer + Tests |
| Unit 6 | Ch 5 | Performance + Vectorization |
| Unit 7 | Ch 3, 12 | Data Acquisition |
| Unit 8 | Ch 4, 7 | Semi-structured Storage |
| Unit 9 | Ch 9 | Data Quality |
| Unit 10 | Ch 4, 6, 7 | ETL/ELT + Medallion |
| Unit 11 | Ch 10, 12 | Git + CI/CD + Docs |

### 2.2 — الطبقات المتراكمة (من المنهج للدليل)

```
📚 المعرفة (Units)
    ↓
🏗️ البناء (Chapters 2,3)
    ↓
🔄 المعالجة (Chapters 4,5,6)
    ↓
📊 التحليل (Chapters 7,8)
    ↓
✅ الجودة (Chapters 9)
    ↓
🚀 الإنتاج (Chapters 10,11)
    ↓
🎯 المبدأ (Chapter 12)
```

---

## 3. نقاط التكامل الحرجة (Critical Integration Points)

### 3.1 — CSV vs Parquet

| الجانب | المنهج (Units 1,5,6) | الدليل (Ch 4) |
|--------|----------------------|---------------|
| **الصيغة** | CSV (Raw + Processed) | Parquet (Analytical) |
| **الحجم** | مقروء بشريًا | مضغوط 70–80% |
| **الاستخدام** | Source of Truth | ML Features |
| **الحل التكاملي** | CSV للـ Bronze/Silver | Parquet للـ Gold |

**التطبيق في v4:**
```
data/bronze/   ← CSV (Raw)
data/silver/   ← CSV (Cleaned)
data/gold/     ← Parquet (Analytics)
```

### 3.2 — Normalization vs Denormalization

| الجانب | المنهج (Unit 4) | الدليل (Ch 7) |
|--------|-----------------|---------------|
| **النموذج** | 3NF | Star Schema |
| **الاستخدام** | OLTP | OLAP |
| **المخرج** | 5 جداول متداخلة | Fact + 4 Dimensions |
| **الحل التكاملي** | 3NF في OLTP | Star في OLAP |

### 3.3 — Single DB vs Multi-Layer

| الجانب | المنهج (Unit 2) | الدليل (Ch 7) |
|--------|-----------------|---------------|
| **المعمارية** | DB واحد | Lakehouse |
| **الحل التكاملي** | Medallion: Bronze/Silver/Gold | |

---

## 4. القواعد الذهبية لعدم التعارض

### قاعدة 1 — لا تُلغِ طبقة، أضِف طبقة
```
❌ لا تحذف CSV     → ✅ أضف Parquet بجانبه
❌ لا تترك 3NF     → ✅ أضف Star Schema فوقه
❌ لا تلغِ SQL     → ✅ أضف Feature Store بجانبه
```

### قاعدة 2 — كل طبقة في مجلدها
```
src/                ← الكود v3.0.0 (يبقى كما هو)
src/warehouse/      ← OLAP Layer (جديد v4)
src/features/       ← Feature Engineering (جديد v4)
src/ml/             ← ML Layer (جديد v4)
docs/               ← التوثيق (موسّع)
```

### قاعدة 3 — اختبارات v3.0.0 مقدّسة
كل مرحلة v4 تنتهي بـ:
```bash
python -m pytest tests/ -q
# يجب أن يبقى: 61 passed
```

### قاعدة 4 — التوثيق قبل الكود
كل مرحلة تبدأ بملف `docs/*.md` يوثق القرار المعماري.

---

## 5. جدول المسارات المستقبلية (v4.0.0)

| المرحلة | المخرج الأساسي | المصدر |
|---------|----------------|--------|
| **0** | `docs/CURRICULUM_MAP.md` + `docs/ARCHITECTURE_LAYERS.md` | المنهج + الدليل |
| **1** | `pipelines/api_pipeline.py` + `scraper_pipeline.py` | Unit 7 |
| **2** | `src/warehouse/parquet_writer.py` + `star_schema.py` | Ch 4, 7 |
| **3** | إعادة تنظيم `data/` → Bronze/Silver/Gold | Ch 7 |
| **4** | `src/features/engineering.py` + `FEATURE_STORE.md` | Unit 9 + Ch 7 |
| **5** | `src/ml/` (split + baseline + trainer + metrics) | ML Day 1 |
| **6** | تحديث CI/CD + Docker + Makefile | Ch 10, 11 |
| **7** | Release v4.0.0 + `PROJECT_STATE_v4.md` | Unit 11 |

**الجدول الزمني الإجمالي:** ~20 يوم عمل

---

## 6. كيفية التحقق من الاتساق

قبل أي commit في v4:
```bash
# 1. كل اختبارات v3.0.0 تعمل
python -m pytest tests/ -q

# 2. الفحوصات الأساسية تعمل
python pipelines/run_all_pipelines.py
python pipelines/compare_pipelines.py

# 3. الوثائق محدّثة
ls docs/   # يجب أن تظهر:
#   CURRICULUM_MAP.md (هذا الملف)
#   ARCHITECTURE_LAYERS.md
#   MEDALLION.md (v4)
#   FEATURE_STORE.md (v4)
#   ...
```

---

## 7. المراجع

- **Course 3 Curriculum:** Units 1–11 (PDF)
- **Guide:** مهارات ومبادئ هندسة البيانات (12 فصلًا)
- **Project:** student-data-pipeline v3.0.0
- **ML:** Applied ML Day 1 (California Housing)

---

**آخر تحديث:** 2026-10-07  
**الإصدار المرتبط:** v3.0.0 → v4.0.0  
**المسؤول:** Galal Al-Ghaberi