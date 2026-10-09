# Playground — Data Quality Exercises

**Purpose:** Practical exercises for Unit 9 (Data Cleaning & Quality).
**Scratch area:** `data/playground/` (gitignored).

---

## Exercise 1 — Add Student 1009 (Basic)

**Date:** 2026-10-09

**Goal:** Add a new student with 1 course + 2 assessments.

**Result:**
- students:    8 → 9
- enrollments: 13 → 14
- assessments: 26 → 28
- 1009: avg_score=87.50, rank=4

**Lesson:** SQL `;` vs `,` — one semicolon per INSERT.

---

## Exercise 2 — Add Second Course

**Date:** 2026-10-09

**Goal:** Enroll 1009 in Database Systems (course 102).

**Result:**
- enrollments: 14 → 15
- assessments: 28 → 30
- 1009: avg_score=82.50 (⬇️), rank=6 (⬇️)

**Lesson:** Adding grades below average → average drops → rank drops.

---

## Exercise 3 — SQLite FK Enforcement

**Date:** 2026-10-10

**Discovery:** SQLite disables FK enforcement by default.
- `sqlite3.connect()` → FK OFF
- `db_layer.connect()` → FK ON (via PRAGMA)

**Fix:** 3 regression tests + defensive verification.

**Lesson:** Every DB has its own quirks. Read the code before testing.

---

## Exercise 4 — 7 Hidden Errors in CSV

**Date:** 2026-10-10

**Errors Detected (7/7):**
| # | Row | Column | Error |
|---|---|---|---|
| 1 | 1002 | age | -5 |
| 2 | 1003 | gpa | 5.5 |
| 3 | 1004 | attendance | 150 |
| 4 | 1005 | gpa | missing |
| 5 | 1001 (r7) | student_id | duplicate |
| 6 | 1007 | age | 999 |
| 7 | 1008 | name | whitespace |

**Subtle Lessons:**
- `str.strip()` ≠ full whitespace normalization
  → Use `.replace(r'\s+', ' ', regex=True)`
- `NaN.between()` returns `False`
  → Separate "out of range" from "missing"
- Median imputation promotes `int` → `float`
  → Restore with `.round().astype(int)`
- **Layered approach:** detect → isolate → impute → restore

**Reference:** Unit 9 (Data Cleaning) + Guide Ch 9.

---

**Last Updated:** 2026-10-10