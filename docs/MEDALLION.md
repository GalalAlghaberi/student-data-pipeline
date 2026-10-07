# 🥉🥈🥇 معمارية الوسام — Medallion Architecture

> **الغرض:** توثيق الطبقات الثلاث (Bronze / Silver / Gold) في مشروع
> Student Data Pipeline، تماشيًا مع Ch 7 من دليل مبادئ هندسة البيانات.

**الإصدار:** v4.0.0-dev  
**المسؤول:** Galal Al-Ghaberi  
**المرجع:** Data Engineering Guide — Ch 4 (Storage) + Ch 7 (Warehouse)

---

## 🎯 الفكرة الأساسية

**Medallion Architecture** = تنظيم البيانات في **ثلاث طبقات متتالية**، كل طبقة ترفع مستوى الجودة والتجميع:

```
RAW → BRONZE → SILVER → GOLD → ML
      (as-is)  (clean)  (analytics)
```

### لماذا ثلاث طبقات؟

| الطبقة | القيمة المضافة |
|---|---|
| **Bronze** | حفظ الأصل كما هو (source of truth) |
| **Silver** | بيانات نظيفة موحدة المخطط |
| **Gold** | جداول تحليلية (Star Schema) جاهزة للاستعلام |

---

## 1. الطبقات الثلاث

### 🥉 Bronze — الطبقة الخام

| البُعد | القيمة |
|---|---|
| **الاسم** | Bronze / Raw Layer |
| **الهدف** | حفظ البيانات الأصلية بدون تعديل |
| **الصيغة** | الأصلية (CSV، JSON، HTML، DB) |
| **التحويل** | لا يوجد — البيانات كما وصلت |
| **المكان** | `data/raw/` (حاليًا) |

**المحتوى الحالي في المشروع:**
```
data/raw/
├── students_raw.csv          ← المصدر الأصلي (CSV)
├── students_raw.json         ← المصدر الأصلي (JSON)
├── university.db             ← OLTP (SQLite)
├── api_students.json         ← Cached API response
├── web_students.html         ← HTML fixture
└── student_data.db           ← Unit 1 SQLite
```

**القاعدة الذهبية:**
> **لا تعدّل Bronze أبدًا.** إذا اكتشفت خطأ، أنشئ معالجة جديدة في Silver.

---

### 🥈 Silver — الطبقة النظيفة

| البُعد | القيمة |
|---|---|
| **الاسم** | Silver / Cleaned Layer |
| **الهدف** | بيانات نظيفة موحدة المخطط |
| **الصيغة** | CSV (نفس v3.0.0) |
| **التحويل** | Extract → Transform → Validate |
| **المكان** | `data/processed/<source>/` (حاليًا) |

**المحتوى الحالي (7 مصادر):**
```
data/processed/
├── csv/csv_clean.csv
├── sqlite/sqlite_clean.csv
├── postgres/postgres_clean.csv
├── mongodb/mongodb_clean.csv
├── json/json_clean.csv
├── api/api_clean.csv         ← جديد v3.0.0+
└── scraper/scraper_clean.csv ← جديد v3.0.0+
```

**المخطط الموحّد (6 أعمدة):**
```
student_id · name · age · gpa · attendance · city
```

**العمليات المطبقة:**
- Type Conversion (`pd.to_numeric`)
- Duplicate Removal (`drop_duplicates`)
- Range Validation (`between`)
- Text Normalization (`.str.strip().title()`)
- Missing Handling (median imputation أو NULL)

**المصدر المنهجي:** Unit 5 + Unit 9  
**التوثيق المفصل:** `docs/DATA_LINEAGE.md`

---

### 🥇 Gold — الطبقة التحليلية

| البُعد | القيمة |
|---|---|
| **الاسم** | Gold / Analytical Layer |
| **الهدف** | Star Schema للتحليلات والـ ML |
| **الصيغة** | Parquet (Column-based) |
| **التحويل** | Star Schema Builder |
| **المكان** | `data/gold/*.parquet` 🆕 |

**المحتوى المتوقع (6 ملفات):**
```
data/gold/
├── dim_students.parquet              ← 1 row = 1 student
├── dim_courses.parquet               ← 1 row = 1 course
├── dim_instructors.parquet           ← 1 row = 1 instructor
├── dim_time.parquet                  ← 1 row = 1 date
├── fact_student_performance.parquet  ← 1 row = 1 assessment
└── fact_enrollment.parquet           ← 1 row = 1 enrollment
```

**لماذا Parquet؟**
- Column-based → قراءة أسرع 5-10x للتحليلات
- ضغط 70-80% مع snappy
- Predicate Pushdown → قراءة الأعمدة المطلوبة فقط
- Schema محفوظ داخل الملف

**المصدر من الدليل:** Ch 4 (Storage) + Ch 7 (Star Schema)

---

## 2. مخطط التدفق الكامل (Data Flow)

```
┌──────────────────────────────────────────────────────────────┐
│                    BRONZE (Raw)                              │
│  data/raw/                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ CSV      │ │ JSON     │ │ SQLite   │ │ HTML     │        │
│  │ 8 rows   │ │ 3 rows   │ │ 8 rows   │ │ 10 rows  │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  + PostgreSQL + MongoDB + API (شبكة/cache)                  │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          │  [ 7 PIPELINES ]
                          │  Extract → Transform → Validate
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    SILVER (Cleaned)                          │
│  data/processed/<source>/<source>_clean.csv                  │
│  ┌──────────────────────────────────────────────────┐        │
│  │ 77 rows total · 6 standard columns               │        │
│  │ student_id · name · age · gpa · attendance · city│        │
│  └──────────────────────────────────────────────────┘        │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          │  [ STAR SCHEMA BUILDER ]
                          │  src/warehouse/star_schema.py
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    GOLD (Analytics)                          │
│  data/gold/*.parquet                                         │
│  ┌─────────────────────────────────────────────────┐         │
│  │  Facts (2):                                     │         │
│  │    fact_student_performance                     │         │
│  │    fact_enrollment                              │         │
│  │                                                  │         │
│  │  Dimensions (4):                                │         │
│  │    dim_students · dim_courses                   │         │
│  │    dim_instructors · dim_time                   │         │
│  └─────────────────────────────────────────────────┘         │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          │  [ ML INTEGRATION ] (المرحلة 5)
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                    ML LAYER (Model)                          │
│  ml_features.parquet · model_metrics.csv                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. الحالة الحالية مقابل المستهدفة

| الطبقة | v3.0.0 | v4.0.0 (الآن) |
|---|---|---|
| **Bronze** | `data/raw/` | `data/raw/` ✅ |
| **Silver** | `data/processed/<source>/` | `data/processed/<source>/` ✅ |
| **Gold** | ❌ غير موجودة | `data/gold/*.parquet` 🆕 |

**ملاحظة:** إعادة التسمية إلى `data/bronze/` و `data/silver/` **لم تُطبّق بعد** — قرار مؤجل للمرحلة 3.

**السبب:** تجنب كسر 7 pipelines و 114 اختبار في v3.0.0. الأولوية الآن هي **إضافة** Gold Layer، ثم **إعادة التنظيم** لاحقًا.

---

## 4. مقارنة معمارية: قبل وبعد

### قبل (v3.0.0) — طبقتان فقط

```
Raw → Processed (CSV)
```

**المشكلة:**
- لا يوجد فصل واضح بين OLTP و OLAP
- التحليلات تحتاج JOINs معقدة
- كل استعلام يقرأ 6 أعمدة كاملة

### بعد (v4.0.0) — ثلاث طبقات

```
Raw → Processed (CSV) → Gold (Parquet + Star Schema)
```

**المزايا:**
- ✅ فصل واضح: OLTP vs OLAP
- ✅ Star Schema = استعلامات أسرع
- ✅ Parquet = قراءة انتقائية
- ✅ جاهز لـ ML feature engineering

---

## 5. متى تستخدم كل طبقة؟

| السؤال | الطبقة |
|---|---|
| ما هي القيمة الأصلية؟ | Bronze |
| ما هو عدد الطلاب الفريدين؟ | Silver |
| ما هي أعلى درجة لكل مقرر؟ | **Gold** |
| ما هو متوسط GPA لكل مدينة؟ | **Gold** |
| من هم الطلاب الذين لم يسجلوا في مقرر؟ | **Gold** |
| كيف أقارن مصادر البيانات؟ | Silver (`compare_pipelines`) |

---

## 6. Grain Definition (Ch 8)

> **القاعدة:** كل جدول له "حبة" (grain) واضحة — ماذا يمثل الصف الواحد؟

### Bronze Layer

| الملف | Grain |
|---|---|
| `students_raw.csv` | 1 row = 1 raw row (كما هو) |
| `university.db` | 5 جداول (OLTP — Grain محدد في `DATABASE.md`) |

### Silver Layer

| الملف | Grain |
|---|---|
| `<source>_clean.csv` | 1 row = 1 student (لكل مصدر) |

### Gold Layer

| الجدول | Grain |
|---|---|
| `dim_students` | 1 row = 1 student |
| `dim_courses` | 1 row = 1 course |
| `dim_instructors` | 1 row = 1 instructor |
| `dim_time` | 1 row = 1 calendar date |
| `fact_student_performance` | **1 row = 1 assessment** |
| `fact_enrollment` | **1 row = 1 enrollment** |

**⚠️ تحذير:** عدم فهم Grain قد يؤدي إلى **Row Multiplication** عند JOINs.

---

## 7. إعادة التوليد (Regeneration)

### إعادة بناء Gold Layer
```bash
python -m src.warehouse.star_schema
```

**المدة المتوقعة:** <1 ثانية

### التحقق من النتائج
```bash
ls -la data/gold/
```

**المتوقع:** 6 ملفات `.parquet`

### متى يجب إعادة التوليد؟
- بعد تحديث `university.db`
- بعد إضافة أعمدة جديدة للـ Fact
- عند تغيير نوع الضغط (snappy → zstd)

---

## 8. لماذا `data/gold/` في `.gitignore`؟

`data/gold/*.parquet` **مستثنى من Git** لأن:

1. **قابل لإعادة التوليد بأمر واحد** (`python -m src.warehouse.star_schema`)
2. **حجمه قد يكون كبيرًا** مع بيانات حقيقية
3. **يمنع Git من تتبع تغييرات ثنائية** (binary diffs)
4. **نفس منطق `data/processed/`** في v3.0.0

**الاستثناء:**
- `.gitkeep` (لحفظ المجلد الفارغ — سنضيفه في المرحلة 3)

**المرجع:** `.gitignore:59`

---

## 9. العلاقة بـ Data Lineage

**Bronze → Silver:**  
موثّق بالتفصيل في `docs/DATA_LINEAGE.md` (7 مصادر × 6 أعمدة)

**Silver → Gold:**  
موثّق في هذا الملف (القسم 2 + القسم 6) وفي `src/warehouse/star_schema.py` (docstrings)

**Gold → ML:**  
سيُوثَّق في المرحلة 4 (`docs/FEATURE_STORE.md`)

---

## 10. خريطة الطريق المستقبلية

| المرحلة | الإجراء | الحالة |
|---|---|---|
| **v4.0.0 (الآن)** | Gold Layer أولي (`data/gold/`) | 🔄 قيد التنفيذ |
| **v4.1.0** | إعادة تسمية Bronze/Silver | ⏳ |
| **v4.2.0** | Feature Store (ML features) | ⏳ |
| **v5.0.0** | Airflow / Dagster orchestration | 🎯 |

**ملاحظة:** كل خطوة تراكمية — **لا نحذف شيئًا**.

---

## 11. المراجع

| المرجع | الغرض |
|---|---|
| `docs/CURRICULUM_MAP.md` | ربط Units بفصول الدليل |
| `docs/ARCHITECTURE_LAYERS.md` | OLTP/OLAP/ML layers |
| `docs/DATA_LINEAGE.md` | نسب الحقول (Bronze → Silver) |
| `src/warehouse/parquet_writer.py` | أدوات Parquet |
| `src/warehouse/star_schema.py` | باني Star Schema |
| `tests/test_warehouse.py` | اختبارات الطبقة |
| **Data Engineering Guide** | Ch 4 + Ch 7 |

---

## 12. المصطلحات (Glossary)

| المصطلح | التعريف |
|---|---|
| **Bronze** | الطبقة الخام — بيانات المصدر بدون تعديل |
| **Silver** | الطبقة النظيفة — موحدة المخطط |
| **Gold** | الطبقة التحليلية — Star Schema |
| **Star Schema** | نموذج: Fact tables + Dimension tables |
| **Fact Table** | جدول الأحداث والقياسات |
| **Dimension** | جدول وصفي للتصفية والتجميع |
| **Grain** | ماذا يمثل الصف الواحد |
| **Parquet** | صيغة ملفات عمودية |
| **Predicate Pushdown** | قراءة انتقائية للأعمدة |

---

**آخر تحديث:** 2026-10-07  
**الإصدار المرتبط:** v4.0.0-dev  
**المسؤول:** Galal Al-Ghaberi