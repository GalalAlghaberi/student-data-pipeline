# PostgreSQL Setup Guide

> Step-by-step guide to installing PostgreSQL and setting up the University Training Database.

---

## Prerequisites

- Windows 10/11 (or Linux/macOS)
- Administrator access (for installation)
- ~500 MB free disk space

---

## Step 1: Install PostgreSQL 18

### Option A: Windows Installer

1. Navigate to `D:\install\`
2. Run: `postgresql-18.6-3-windows-x64.exe`
3. During installation:
   - **Port:** `5432` (default)
   - **Superuser password:** Choose a strong password (e.g., `admin1234`)
   - **⚠️ Save this password — you'll need it later**
   - **Locale:** English (or your preference)
4. Complete installation

### Option B: Package Manager

```bash
# Chocolatey
choco install postgresql18

# Scoop
scoop install postgresql
```

### Verify Installation

```bash
psql --version
# Expected: psql (PostgreSQL) 18.x
```

---

## Step 2: Install pgAdmin 4

**pgAdmin** is the GUI for PostgreSQL.

Download from: https://www.pgadmin.org/download/

After installation, launch **pgAdmin 4**.

---

## Step 3: Register the Server

### 3.1 Open pgAdmin

You'll see an empty **Object Explorer** on the left.

### 3.2 Add Server

1. **Right-click** on `Servers` in the left tree
2. Select: `Register → Server...`

### 3.3 Fill Connection Info

**General tab:**
```
Name:  Local PostgreSQL
```

**Connection tab:**
```
Host name/address:     localhost
Port:                  5432
Maintenance database:  postgres
Username:              postgres
Password:              [your password]
☑️ Save password
```

3. Click **Save**

**Result:** The server appears in the tree.

---

## Step 4: Create the Database

### 4.1 Expand the Tree

```
Servers
└─ Local PostgreSQL
   └─ Databases
```

### 4.2 Create Database

1. **Right-click** on `Databases`
2. Select: `Create → Database...`
3. Fill:
   ```
   Database:  university_training
   Owner:     postgres
   ```
4. Click **Save**

**Result:** `university_training` appears in the tree.

---

## Step 5: Create Tables

### 5.1 Open Query Tool

1. **Right-click** on `university_training`
2. Select: `Query Tool` (`Ctrl+E`)

### 5.2 Paste Schema

Open `database/queries/postgresql/01_schema.sql` in VS Code and copy its contents.

Or from command line:

```bash
cat database/queries/postgresql/01_schema.sql
```

Paste into the Query Tool.

### 5.3 Execute

Press **`F5`** (or click ▶ button).

**Expected:** `CREATE TABLE` and `CREATE INDEX` messages.

### 5.4 Verify Tables Created

In the left tree:
```
university_training
└─ Schemas
   └─ public
      └─ Tables (5)
         ├─ assessments
         ├─ courses
         ├─ enrollments
         ├─ instructors
         └─ students
```

---

## Step 6: Insert Sample Data

### 6.1 Open New Query Tool

`Ctrl+E` or right-click → Query Tool.

### 6.2 Paste Seed Data

Copy contents of `database/queries/postgresql/02_seed_data.sql`.

### 6.3 Execute

**`F5`** → `INSERT 0 1` messages.

### 6.4 Verify Data

Run `03_verify.sql`:

```sql
SELECT 'instructors' AS table_name, COUNT(*) FROM instructors
UNION ALL SELECT 'students',    COUNT(*) FROM students
UNION ALL SELECT 'courses',     COUNT(*) FROM courses
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments
UNION ALL SELECT 'assessments', COUNT(*) FROM assessments;
```

**Expected:**

| table_name | count |
|------------|-------|
| instructors | 4 |
| students | 8 |
| courses | 5 |
| enrollments | 13 |
| assessments | 26 |

---

## Step 7: Run Your First Advanced Query

Open a new Query Tool and paste:

```sql
WITH student_avg AS (
    SELECT
        s.student_id,
        s.full_name,
        s.city,
        ROUND(AVG(a.score)::numeric, 2) AS average_score
    FROM students s
    JOIN assessments a ON s.student_id = a.student_id
    GROUP BY s.student_id, s.full_name, s.city
)
SELECT
    student_id,
    full_name,
    city,
    average_score,
    RANK() OVER (ORDER BY average_score DESC) AS student_rank
FROM student_avg
ORDER BY student_rank;
```

**Expected:** 8 students ranked by average score.

---

## Troubleshooting

### "Cannot connect to server"

**Cause:** PostgreSQL service not running.

**Fix (Windows):**
1. Open **Services** (`Win+R` → `services.msc`)
2. Find `postgresql-x64-18`
3. Right-click → **Start**

### "Password authentication failed"

**Cause:** Wrong password.

**Fix:**
- Right-click server → Properties → Connection → Update password
- Or reset via `pg_hba.conf`

### "Database already exists"

**Cause:** You already created it.

**Fix:** Skip to Step 5 (create tables).

### "Relation already exists"

**Cause:** You're re-running `01_schema.sql`.

**Fix:** Skip it, or drop tables first:

```sql
DROP TABLE IF EXISTS assessments, enrollments, courses, students, instructors CASCADE;
```

---

## Useful pgAdmin Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+E` | New Query Tool |
| `F5` | Execute query |
| `Ctrl+O` | Open SQL file |
| `Ctrl+S` | Save current file |
| `Shift+F5` | Execute current statement only |
| `F7` | EXPLAIN ANALYZE |
| `Ctrl+Shift+F` | Format SQL |

---

## Connecting from Python

To connect from Python (later units):

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="university_training",
    user="postgres",
    password="your_password"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM students")
print(cursor.fetchone())

conn.close()
```

**Note:** `psycopg2-binary` is already installed in your environment.

---

## Related Files

- **PostgreSQL queries:** [`database/queries/postgresql/`](../database/queries/postgresql/)
- **ERD + constraints:** [`docs/DATABASE.md`](DATABASE.md)
- **Main README:** [`README.md`](../README.md)

---

## Verification Checklist

After setup, you should be able to:

- [ ] Connect to `university_training` in pgAdmin
- [ ] See 5 tables in the tree
- [ ] Run `SELECT * FROM students;` and see 8 rows
- [ ] Run the first advanced query (student ranking)
- [ ] Execute SQL files from `database/queries/postgresql/`

---

**Last updated:** 2026-10-05