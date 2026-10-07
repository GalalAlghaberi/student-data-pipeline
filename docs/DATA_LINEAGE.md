# 🔗 نسب البيانات — Data Lineage

> **الغرض:** توثيق رحلة كل حقل بيانات من مصدره الخام إلى المخرج النهائي
> الموحّد، عبر 7 pipelines و 4 مراحل معالجة (Extract → Transform → Validate → Load).

**الإصدار:** v3.0.0 (يُحدَّث في v4.0.0 بـ ML features)  
**المرجع المنهجي:** Unit 10 + Unit 11  
**المسؤول:** Galal Al-Ghaberi

---

## 🎯 ما هو Data Lineage؟

**Data Lineage** = قدرة الفريق على الإجابة عن السؤال:

> **"من أين جاءت هذه القيمة؟ وما التعديلات التي مرّت عليها؟"**

### لماذا هو مهم؟

| السبب | الفائدة |
|---|---|
| **Debugging** | تتبّع خطأ من المخرج إلى المصدر |
| **Auditing** | إثبات أن البيانات من مصدر موثوق |
| **Reproducibility** | إعادة توليد نفس النتيجة |
| **Governance** | معرفة من يملك كل حقل |
| **Quality Control** | تحديد أين تنشأ المشاكل |

### مثال عملي

```
القيمة: gpa = 3.75 للطالب 3001

المصدر:    data/raw/web_students.html (سطر 42)
المرحلة 1: ScraperPipeline.extract() → 3.75 (string → "3.75")
المرحلة 2: ScraperPipeline.transform() → float64(3.75)
المرحلة 3: ScraperPipeline.validate() → ✓ 0 ≤ 3.75 ≤ 4
المرحلة 4: Load → data/processed/scraper/scraper_clean.csv
```

---

## 1. المخطط الموحّد (Standard Schema)

كل pipeline في المشروع يُنتج **نفس الأعمدة الستة** بالترتيب نفسه:

| # | العمود | النوع | الوصف | القيد |
|---|---|---|---|---|
| 1 | `student_id` | Int64 | معرّف الطالب | فريد، لا NULL |
| 2 | `name` | string | الاسم الكامل | لا NULL |
| 3 | `age` | Int64 | العمر | 16–80 |
| 4 | `gpa` | float64 | المعدل التراكمي | 0–4 (يُسمح بـ NULL لبعض المصادر) |
| 5 | `attendance` | float64 | نسبة الحضور | 0–100 (يُسمح بـ NULL لبعض المصادر) |
| 6 | `city` | string | المدينة | لا NULL |

**المصدر المرجعي:** `pipelines/base_pipeline.py`  
```python
STANDARD_COLUMNS = ["student_id", "name", "age", "gpa", "attendance", "city"]
```

---

## 2. مصفوفة المصادر (Source Matrix)

### 2.1 نظرة سريعة على 7 pipelines

| # | Pipeline | المصدر | الصيغة | صفوف | الحقول الناقصة |
|---|---|---|---|---|---|
| 1 | `CSVPipeline` | `data/raw/students_raw.csv` | CSV | 8 | — |
| 2 | `SQLitePipeline` | `data/raw/university.db` | SQLite | 8 | `attendance` |
| 3 | `PostgresPipeline` | `localhost:5432` | PostgreSQL | 8 | `attendance` |
| 4 | `MongoDBPipeline` | `localhost:27017` | MongoDB | 10 | — |
| 5 | `JSONPipeline` | `data/raw/students_raw.json` | JSON | 3 | — |
| 6 | `APIPipeline` | `dummyjson.com/users` | REST API | 30 | `gpa`, `attendance` |
| 7 | `ScraperPipeline` | `data/raw/web_students.html` | HTML | 10 | — |

**إجمالي:** 77 صفًا × 6 أعمدة = **462 خلية**.

### 2.2 لماذا بعض المصادر ناقصة؟

**هذا ليس خطأ** — بل انعكاس لواقع البيانات:

- **SQLite/Postgres:** مصمّمة في v2.0.0 قبل إضافة `attendance` → القيد معروف
- **API (DummyJSON):** يوفر بيانات مستخدم عامة، لا بيانات أكاديمية
- **هذه الفروق يُكشفها:** `compare_pipelines.py` → `missing_values` column

---

## 3. نسب البيانات التفصيلي (Field-by-Field)

### 3.1 `student_id` — معرّف الطالب

| المصدر | الحقل الخام | نوع خام | التحويل |
|---|---|---|---|
| CSV | `student_id` | string | `pd.to_numeric(errors="coerce")` → Int64 |
| SQLite | `student_id` | INTEGER | تمرير مباشر |
| Postgres | `student_id` | INTEGER | تمرير مباشر |
| MongoDB | `student_id` | int32 | `astype("Int64")` |
| JSON | `student_id` | int | `astype("Int64")` |
| **API** | `id` | int | `pd.to_numeric(df["id"])` → Int64 |
| Scraper | `cells[0].text` | string | `_to_int(cells[0])` → Int64 |

**قواعد الجودة:**
- ✅ فريد (`is_unique`)
- ✅ لا NULL (`notna().all()`)

### 3.2 `name` — الاسم الكامل

| المصدر | الحقل الخام | التحويل |
|---|---|---|
| CSV | `name` | `.str.strip()` |
| SQLite | `full_name` | **إعادة تسمية** + `.str.strip()` |
| Postgres | `full_name` | **إعادة تسمية** + `.str.strip()` |
| MongoDB | `personal.name` (nested) | `json_normalize` + `astype("string")` |
| JSON | `name` | `astype("string")` |
| **API** | `firstName` + `lastName` | **دمج:** `firstName + " " + lastName` + `.str.strip()` |
| Scraper | `cells[1].text` | `_clean_text(cells[1])` + `.str.replace(r"\s+", " ")` |

**قواعد الجودة:**
- ✅ لا NULL
- ✅ تنظيف المسافات المتكررة

### 3.3 `age` — العمر

| المصدر | الحقل الخام | التحويل |
|---|---|---|
| CSV | `age` | `pd.to_numeric` → Int64 |
| SQLite | `age` | تمرير مباشر |
| Postgres | `age` | تمرير مباشر |
| MongoDB | `personal.age` | `json_normalize` → Int64 |
| JSON | `age` | `astype("Int64")` |
| API | `age` | `pd.to_numeric(df["age"])` |
| Scraper | `cells[2].text` | `_to_int(cells[2])` → Int64 |

**قواعد الجودة:**
- ✅ 16 ≤ age ≤ 80
- ⚠️ القيم الشاذة (سالب، > 200) تُحوّل إلى `pd.NA` ثم تُملأ بـ median

### 3.4 `gpa` — المعدل التراكمي

| المصدر | الحقل الخام | التحويل | NULL مسموح؟ |
|---|---|---|---|
| CSV | `gpa` | `pd.to_numeric` → float64 | لا |
| SQLite | **غير موجود** | — | **نعم (NULL)** |
| Postgres | **غير موجود** | — | **نعم (NULL)** |
| MongoDB | `academic.gpa` (nested) | `json_normalize` → float64 | لا |
| JSON | `gpa` | `astype("float64")` | لا |
| API | **غير موجود** | `pd.NA` | **نعم (NULL)** |
| Scraper | `cells[3].text` | `_to_float(cells[3])` | لا |

**قواعد الجودة:**
- ✅ 0 ≤ gpa ≤ 4
- ✅ NULL مسموح في SQLite, Postgres, API (بسبب غياب الحقل الخام)

### 3.5 `attendance` — نسبة الحضور

| المصدر | الحقل الخام | التحويل | NULL مسموح؟ |
|---|---|---|---|
| CSV | `attendance` | `pd.to_numeric` → float64 | لا |
| SQLite | **غير موجود** | — | **نعم (NULL)** |
| Postgres | **غير موجود** | — | **نعم (NULL)** |
| MongoDB | `academic.attendance` (nested) | `json_normalize` → float64 | لا |
| JSON | `attendance` | `astype("float64")` | لا |
| API | **غير موجود** | `pd.NA` | **نعم (NULL)** |
| Scraper | `cells[4].text` | `_to_float(cells[4])` | لا |

**قواعد الجودة:**
- ✅ 0 ≤ attendance ≤ 100
- ✅ NULL مسموح في SQLite, Postgres, API

### 3.6 `city` — المدينة

| المصدر | الحقل الخام | التحويل |
|---|---|---|
| CSV | `city` | `.str.strip().str.title()` |
| SQLite | `city` | `.str.strip().str.title()` |
| Postgres | `city` | `.str.strip().str.title()` |
| MongoDB | `personal.city` (nested) | `json_normalize` + `.str.title()` |
| JSON | `city` | `.str.strip().str.title()` |
| **API** | `address.city` (nested) | `df["address"].apply(lambda a: a.get("city"))` |
| Scraper | `cells[5].text` | `_clean_text(cells[5])` + `.str.title()` |

**قواعد الجودة:**
- ✅ لا NULL
- ✅ Title case موحّد (`Sanaa` لا `sanaa` ولا `SANAA`)

---

## 4. تحويلات عامة (Common Transformations)

تطبَّق على **جميع المصادر** في `transform_layer.py`:

| التحويل | الدالة | الغرض |
|---|---|---|
| **Type Conversion** | `pd.to_numeric(errors="coerce")` | إجبار الأنواع |
| **Text Cleaning** | `.str.strip()` | إزالة المسافات |
| **Text Standardization** | `.str.title()` | توحيد المدينة |
| **Whitespace Collapse** | `.str.replace(r"\s+", " ")` | طي المسافات المتكررة |
| **Duplicate Removal** | `drop_duplicates(subset=["student_id"])` | إزالة التكرار |
| **Range Clamping** | `.where(.between(lo, hi))` | وضع حدود للنطاقات |
| **Missing Imputation** | `.fillna(median)` | ملء الفراغات |

**المرجع:** `src/transform_layer.py`

---

## 5. بوابات الجودة (Quality Gates)

### 5.1 Layers of Validation

```
Layer 1: Schema Validation  → الأعمدة الستة موجودة
Layer 2: Type Validation     → الأنواع صحيحة
Layer 3: Range Validation    → القيم ضمن الحدود
Layer 4: Uniqueness           → student_id فريد
Layer 5: Completeness         → الحقول المطلوبة ليست NULL
```

**المرجع:** `src/validate_layer.py` + `docs/DATABASE.md`

### 5.2 Fail-Fast vs Quarantine

| السيناريو | الإجراء |
|---|---|
| **حقل مطلوب NULL** | ❌ Fail-Fast (Pipeline يتوقف) |
| **قيمة خارج النطاق** | ⚠️ Quarantine (تُنقل إلى `students_invalid.csv`) |
| **تكرار في student_id** | ❌ Fail-Fast |
| **gpa/attendance NULL** | ✅ مسموح (يُسجَّل في `missing_count`) |

---

## 6. مخطط التتبع (Traceability Diagram)

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAW SOURCES                                │
│  CSV · SQLite · PostgreSQL · MongoDB · JSON · API · HTML        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  [ EXTRACT ]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SOURCE-SPECIFIC RAW (as-is)                        │
│  • CSV      → pd.read_csv                                       │
│  • SQLite   → sqlite3 + read_sql_query                          │
│  • API      → requests + cache fallback                         │
│  • Scraper  → BeautifulSoup                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  [ TRANSFORM ]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              STANDARD SCHEMA (6 columns)                        │
│  student_id · name · age · gpa · attendance · city              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  [ VALIDATE ]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY GATES                                │
│  Schema ✓ · Types ✓ · Ranges ✓ · Uniqueness ✓ · Completeness ✓  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  [ LOAD ]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                data/processed/<source>/                         │
│  <source>_clean.csv  (7 ملفات)                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │  [ COMPARE ]
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                data/comparison/                                 │
│  comparison_data.csv · comparison_report.md                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. أمثلة عملية للتتبع (Worked Examples)

### مثال 1: الطالب 1001 من CSV

```
INPUT (CSV):
    1001,Ahmed Ali,22,3.50,92,Sanaa

STEP 1 — Extract:
    {"student_id": "1001", "name": "Ahmed Ali", "age": "22",
     "gpa": "3.50", "attendance": "92", "city": "Sanaa"}

STEP 2 — Transform:
    {"student_id": 1001, "name": "Ahmed Ali", "age": 22,
     "gpa": 3.50, "attendance": 92.0, "city": "Sanaa"}

STEP 3 — Validate:
    ✓ student_id=1001 فريد
    ✓ 16 ≤ 22 ≤ 80
    ✓ 0 ≤ 3.50 ≤ 4
    ✓ 0 ≤ 92 ≤ 100

STEP 4 — Load:
    data/processed/csv/csv_clean.csv :: row 0
```

### مثال 2: الطالب 3001 من API

```
INPUT (DummyJSON):
    {"id": 3001, "firstName": "Ahmed", "lastName": "Al-Sanaani",
     "age": 22, "address": {"city": "Sanaa"}}

STEP 1 — Extract:
    Raw dict (28 fields from DummyJSON)

STEP 2 — Transform:
    student_id ← id (3001)
    name       ← firstName + " " + lastName ("Ahmed Al-Sanaani")
    age        ← age (22)
    gpa        ← NaN   [NOT PROVIDED BY API]
    attendance ← NaN   [NOT PROVIDED BY API]
    city       ← address.city ("Sanaa")

STEP 3 — Validate:
    ✓ student_id=3001 فريد
    ✓ name ليس NULL
    ✓ age في النطاق
    ✓ city ليس NULL
    ℹ gpa/attendance = NULL (مسموح للـ API)

STEP 4 — Load:
    data/processed/api/api_clean.csv :: row 0
```

### مثال 3: الطالب 3001 من Scraper

```
INPUT (web_students.html):
    <tr>
        <td>3001</td>
        <td>Ahmed Al-Sanaani</td>
        <td>22</td>
        <td>3.75</td>
        <td>92</td>
        <td>Sanaa</td>
    </tr>

STEP 1 — Extract (BeautifulSoup):
    cells = row.find_all("td")   # 6 cells
    → _extract_record(cells, 1)

STEP 2 — Transform:
    student_id ← _to_int(cells[0]) = 3001
    name       ← _clean_text(cells[1]) = "Ahmed Al-Sanaani"
    age        ← _to_int(cells[2]) = 22
    gpa        ← _to_float(cells[3]) = 3.75
    attendance ← _to_float(cells[4]) = 92.0
    city       ← _clean_text(cells[5]).title() = "Sanaa"

STEP 3 — Validate:
    ✓ كل القواعد تمر

STEP 4 — Load:
    data/processed/scraper/scraper_clean.csv :: row 0
```

---

## 8. كيف تُستخدم هذه الوثيقة؟

### عند اكتشاف خطأ
1. افتح `comparison_report.md`
2. حدّد أي مصدر فيه المشكلة
3. ارجع إلى القسم 3 (نسب الحقل)
4. اتبع خطوات Extract → Transform → Validate
5. اعرف أين نشأ الخطأ بالضبط

### عند إضافة مصدر جديد
1. أضف صفًا في **Section 2.1**
2. أضف صفًا في **Section 3.x** لكل حقل
3. وثّق التحويلات الخاصة
4. أضف اختبارات `test_<source>_pipeline.py`

### عند تدقيق جودة البيانات
1. استخدم **Section 5 (Quality Gates)**
2. تحقّق من كل طبقة على حدة
3. وثّق النتائج في `quality_report.csv`

---

## 9. خريطة التحديثات المستقبلية

| الإصدار | الإضافة |
|---|---|
| **v3.0.0** | 7 pipelines (هذه الوثيقة) |
| **v4.0.0** | + `ml_features.parquet` + Feature Lineage |
| **v5.0.0** | + Lineage Graphs (DataHub / OpenMetadata) |

---

## 10. المراجع

| المرجع | الغرض |
|---|---|
| `docs/CURRICULUM_MAP.md` | ربط الوحدات بفصول الدليل |
| `docs/ARCHITECTURE_LAYERS.md` | OLTP/OLAP/ML layers |
| `docs/DATABASE.md` | ERD + Schema |
| `src/base_pipeline.py` | STANDARD_COLUMNS |
| `src/transform_layer.py` | Transformations |
| `src/validate_layer.py` | Quality Rules |
| `pipelines/*_pipeline.py` | Source-specific logic |
| `data/comparison/comparison_report.md` | 7-source comparison |

---

**آخر تحديث:** 2026-10-07  
**الإصدار المرتبط:** v3.0.0  
**المسؤول:** Galal Al-Ghaberi