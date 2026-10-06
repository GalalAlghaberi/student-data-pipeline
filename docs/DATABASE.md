\# University Training Database



> A relational database for practicing SQL and Data Engineering concepts, integrated with the main Python pipeline.



\---



\## Overview



The database models a \*\*university training system\*\* with 5 related tables:



| Table | Purpose | Rows |

|---|---|---|

| `instructors` | Teaching staff | 4 |

| `students` | Enrolled students | 8 |

| `courses` | Offered courses | 5 |

| `enrollments` | Student - Course (M:N bridge) | 13 |

| `assessments` | Grades (Midterm/Final/Quiz/Project) | 26 |



Additionally, the project includes a \*\*MongoDB document database\*\* for semi-structured data (see \[MongoDB section](#mongodb--nosql-unit-8) below).



\---



\## Entity-Relationship Diagram



```

+------------------+

|  instructors     |

|------------------|

|  instructor\_id   |<-------+

|  full\_name       |        |

|  department      |        | 1:N

|  email           |        |

+------------------+        |

&#x20;                           |

+--------------+   +--------+--------+

|  students    |   |  courses        |

|--------------|   |-----------------|

|  student\_id  |   |  course\_id      |

|  full\_name   |   |  course\_name    |

|  gender      |   |  credit\_hours   |

|  date\_of\_birth|  |  instructor\_id  |

|  city        |   +--------+--------+

+------+-------+            |

&#x20;      |                    |

&#x20;      | 1:N          1:N   |

&#x20;      v                    v

+----------------------------+

|  enrollments               |

|----------------------------|

|  enrollment\_id (PK)        |

|  student\_id    (FK)        |

|  course\_id     (FK)        |

|  enrollment\_date           |

|  semester                  |

|  UNIQUE(student, course,   |

|         semester)          |

+----------------------------+



&#x20;      | 1:N          1:N   |

&#x20;      v                    v

+----------------------------+

|  assessments               |

|----------------------------|

|  assessment\_id (PK)        |

|  student\_id    (FK)        |

|  course\_id     (FK)        |

|  assessment\_type           |

|  score (0-100)             |

+----------------------------+

```



\---



\## Constraints Enforced



| Table | Constraint | Purpose |

|---|---|---|

| `instructors` | `email UNIQUE` | No duplicate emails |

| `students` | `gender CHECK` | Only 'Male' / 'Female' |

| `courses` | `credit\_hours CHECK > 0` | No zero-credit courses |

| `enrollments` | `UNIQUE(student, course, semester)` | Prevent re-enrollment |

| `assessments` | `score CHECK 0-100` | Valid grade range |

| `assessments` | `assessment\_type CHECK` | Only valid types |



\*\*Foreign Keys:\*\*

\- `courses.instructor\_id` -> `instructors.instructor\_id`

\- `enrollments.student\_id` -> `students.student\_id`

\- `enrollments.course\_id` -> `courses.course\_id`

\- `assessments.student\_id` -> `students.student\_id`

\- `assessments.course\_id` -> `courses.course\_id`



\---



\## Query Catalog



| File | Purpose |

|---|---|

| `database/queries/basic.sql` | SELECT, WHERE, ORDER BY |

| `database/queries/aggregates.sql` | COUNT, AVG, MIN, MAX, GROUP BY, HAVING |

| `database/queries/joins.sql` | INNER JOIN, LEFT JOIN, Multi-Table |

| `database/queries/reports.sql` | Analytical reports + ML feature table |

| `database/queries/postgresql/` | PostgreSQL-specific (schema, seed, verify, CASE, subqueries, CTEs, window functions, ranking, LAG/LEAD) |

| `database/queries/advanced/` | SQLite advanced queries |

| `database/mongodb/` | MongoDB query catalog + README |



\---



\## Build \& Export Workflow



```bash

\# 1. Build the SQLite database from scratch

python scripts/build\_university\_db.py



\# 2. Export the ML feature table to CSV

python scripts/export\_student\_report.py

```



\*\*Output:\*\*

\- `data/raw/university.db` - SQLite database

\- `data/processed/student\_performance.csv` - ML-ready features



\---



\## ML Feature Table



The canonical ML-ready table is built via:



```sql

SELECT

&#x20;   s.student\_id,

&#x20;   s.full\_name       AS student\_name,

&#x20;   s.city,

&#x20;   COUNT(DISTINCT e.course\_id) AS courses\_count,

&#x20;   COUNT(a.assessment\_id)      AS assessments\_count,

&#x20;   ROUND(AVG(a.score), 2)      AS average\_score,

&#x20;   MAX(a.score)                AS highest\_score,

&#x20;   MIN(a.score)                AS lowest\_score

FROM students s

LEFT JOIN enrollments e ON s.student\_id = e.student\_id

LEFT JOIN assessments a ON s.student\_id = a.student\_id

GROUP BY s.student\_id, s.full\_name, s.city

ORDER BY average\_score DESC;

```



\*\*Why LEFT JOIN?\*\* Keeps students with no enrollments/assessments (defensive).



\---



\## MongoDB — NoSQL (Unit 8)



In addition to the relational database, the project includes a \*\*document-oriented database\*\* for semi-structured data.



\### Database: `University\_Ai`



| Collection | Purpose | Documents |

|---|---|---|

| `students` | Semi-structured student records | 10 |

| `validated\_students` | JSON Schema validation demo | 0 |



\### Document Schema



```json

{

&#x20; "student\_id": 1001,

&#x20; "personal": {

&#x20;   "name": "Ahmed Ali",

&#x20;   "age": 22,

&#x20;   "city": "Sanaa",

&#x20;   "country": "Yemen"

&#x20; },

&#x20; "skills": \["Python", "SQL", "MongoDB"],

&#x20; "academic": {

&#x20;   "gpa": 3.75,

&#x20;   "attendance": 95

&#x20; },

&#x20; "projects": \[

&#x20;   {

&#x20;     "name": "AI Pipeline",

&#x20;     "year": 2026,

&#x20;     "status": "Completed",

&#x20;     "technologies": \["Python", "PostgreSQL"]

&#x20;   }

&#x20; ]

}

```



\### Indexes



| Index | Fields | Type |

|---|---|---|

| `\_id\_` | `\_id` | Default |

| `student\_id\_1` | `student\_id` | Unique |

| `personal.city\_1` | `personal.city` | Single |

| `academic.gpa\_1` | `academic.gpa` | Single |



\### Access



\- \*\*GUI:\*\* MongoDB Compass (`localhost:27017` -> `University\_Ai`)

\- \*\*Scripts:\*\* `python scripts/mongodb\_read.py`



\### Why MongoDB?



| Aspect | PostgreSQL | MongoDB |

|---|---|---|

| Nested data | Verbose | Native |

| Arrays | Separate table | Embedded |

| Schema evolution | Migrations | Flexible |

| Best for | Structured, relational | Semi-structured, document-oriented |



Full guide: \[docs/MONGODB.md](MONGODB.md)



\---



\## Connection to Units 1, 2, and 8



The database integrates with multiple pipelines:



```

Unit 1 Pipeline:  CSV -> Cleaning -> Validation -> ML-ready CSV

&#x20;                                   ^

&#x20;                                   |

Unit 2 adds:      SQLite DB ---> SQL Extraction ---> Pandas ---> CSV



Unit 8 adds:      5 independent pipelines (CSV, JSON, SQLite, PostgreSQL, MongoDB)

&#x20;                 Each produces data/processed/{source}/{source}\_clean.csv

&#x20;                 Comparison report at data/comparison/comparison\_report.md

```



\*\*All pathways converge on ML-ready datasets.\*\*



\---



\## Testing



| File | Focus | Tests |

|---|---|---|

| `tests/test\_db\_layer.py` | Connection + SQL execution | 10 |

| `tests/test\_query\_layer.py` | SQL -> DataFrame | 9 |



Run all:



```bash

pytest tests/ -v

```



\*\*Total tests: 61\*\*



\---



\## Related Documentation



| Document | Purpose |

|---|---|

| \[README.md](../README.md) | Project overview |

| \[ARCHITECTURE.md](../ARCHITECTURE.md) | Design decisions |

| \[POSTGRESQL\_SETUP.md](POSTGRESQL\_SETUP.md) | PostgreSQL setup guide |

| \[MONGODB.md](MONGODB.md) | MongoDB integration guide |

| \[PIPELINE\_ARCHITECTURE.md](PIPELINE\_ARCHITECTURE.md) | Multi-source pipeline architecture |

