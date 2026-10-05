-- ============================================================
-- Unit 2 — Comprehensive Review (PostgreSQL)
-- University Training Database
-- ============================================================

-- ═══════════════════════════════════════════════════════════
-- SECTION 1: SELECT Basics
-- ═══════════════════════════════════════════════════════════

-- 1.1 — كل الطلاب
SELECT student_id, full_name, city
FROM students
ORDER BY student_id;

-- 1.2 — Aliases (أسماء بديلة)
SELECT
    student_id AS id,
    full_name AS student_name,
    city AS home_city
FROM students;

-- 1.3 — Expressions (تعبيرات حسابية)
SELECT
    course_name,
    credit_hours,
    credit_hours * 2 AS doubled_hours
FROM courses;

-- ═══════════════════════════════════════════════════════════
-- SECTION 2: WHERE — Filtering
-- ═══════════════════════════════════════════════════════════

-- 2.1 — طلاب صنعاء
SELECT student_id, full_name, city
FROM students
WHERE city = 'Sanaa';

-- 2.2 — درجات 90+
SELECT student_id, course_id, score
FROM assessments
WHERE score >= 90
ORDER BY score DESC;

-- 2.3 — AND
SELECT student_id, score
FROM assessments
WHERE score >= 80 AND score < 90
ORDER BY score DESC;

-- 2.4 — OR
SELECT student_id, full_name, city
FROM students
WHERE city = 'Sanaa' OR city = 'Dhamar';

-- 2.5 — NOT
SELECT student_id, full_name, city
FROM students
WHERE NOT city = 'Sanaa';

-- 2.6 — IN (أفضل من OR للمجموعات)
SELECT student_id, full_name, city
FROM students
WHERE city IN ('Sanaa', 'Ibb', 'Taiz');

-- ═══════════════════════════════════════════════════════════
-- SECTION 3: ORDER BY — Sorting
-- ═══════════════════════════════════════════════════════════

-- 3.1 — تنازلي
SELECT assessment_id, score
FROM assessments
ORDER BY score DESC;

-- 3.2 — تصاعدي
SELECT assessment_id, score
FROM assessments
ORDER BY score ASC;

-- 3.3 — متعدد الأعمدة
SELECT student_id, full_name, city
FROM students
ORDER BY city ASC, full_name ASC;

-- 3.4 — LIMIT (أعلى 5 درجات)
SELECT assessment_id, student_id, score
FROM assessments
ORDER BY score DESC
LIMIT 5;

-- ═══════════════════════════════════════════════════════════
-- SECTION 4: Aggregate Functions
-- ═══════════════════════════════════════════════════════════

-- 4.1 — COUNT
SELECT COUNT(*) AS total_students FROM students;

-- 4.2 — AVG
SELECT ROUND(AVG(score)::numeric, 2) AS average_score FROM assessments;

-- 4.3 — MAX / MIN / SUM
SELECT
    MAX(score) AS highest,
    MIN(score) AS lowest,
    SUM(score) AS total,
    COUNT(*)   AS total_records
FROM assessments;

-- ═══════════════════════════════════════════════════════════
-- SECTION 5: GROUP BY
-- ═══════════════════════════════════════════════════════════

-- 5.1 — عدد الطلاب في كل مدينة
SELECT city, COUNT(*) AS student_count
FROM students
GROUP BY city
ORDER BY student_count DESC;

-- 5.2 — متوسط الدرجات لكل طالب
SELECT
    student_id,
    ROUND(AVG(score)::numeric, 2) AS average_score
FROM assessments
GROUP BY student_id
ORDER BY average_score DESC;

-- 5.3 — متوسط الدرجات لكل مقرر
SELECT
    course_id,
    ROUND(AVG(score)::numeric, 2) AS average_score
FROM assessments
GROUP BY course_id
ORDER BY average_score DESC;

-- ═══════════════════════════════════════════════════════════
-- SECTION 6: HAVING — Filtering Groups
-- ═══════════════════════════════════════════════════════════

-- 6.1 — الطلاب المتفوقون (متوسط 85+)
SELECT
    student_id,
    ROUND(AVG(score)::numeric, 2) AS average_score
FROM assessments
GROUP BY student_id
HAVING AVG(score) >= 85
ORDER BY average_score DESC;

-- 6.2 — المدن التي فيها 2+ طلاب
SELECT city, COUNT(*) AS student_count
FROM students
GROUP BY city
HAVING COUNT(*) >= 2
ORDER BY student_count DESC;

-- ═══════════════════════════════════════════════════════════
-- SECTION 7: INNER JOIN
-- ═══════════════════════════════════════════════════════════

-- 7.1 — الطلاب ومقرراتهم
SELECT
    s.student_id,
    s.full_name AS student_name,
    e.course_id
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
ORDER BY s.student_id;

-- 7.2 — الطلاب + أسماء المقررات (3 جداول)
SELECT
    s.full_name AS student_name,
    c.course_name
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses c     ON e.course_id  = c.course_id
ORDER BY s.full_name, c.course_name;

-- 7.3 — الطلاب + المقررات + المدرسين (4 جداول)
SELECT
    s.full_name  AS student_name,
    c.course_name,
    i.full_name  AS instructor_name
FROM students s
INNER JOIN enrollments e ON s.student_id    = e.student_id
INNER JOIN courses c     ON e.course_id     = c.course_id
INNER JOIN instructors i ON c.instructor_id = i.instructor_id
ORDER BY student_name;

-- ═══════════════════════════════════════════════════════════
-- SECTION 8: LEFT JOIN
-- ═══════════════════════════════════════════════════════════

-- 8.1 — كل الطلاب مع تسجيلاتهم
SELECT
    s.student_id,
    s.full_name,
    e.course_id
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
ORDER BY s.student_id;

-- 8.2 — الطلاب غير المسجلين في أي مقرر
SELECT s.student_id, s.full_name
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
WHERE e.student_id IS NULL;

-- 8.3 — عدد الطلاب في كل مقرر
SELECT
    c.course_name,
    COUNT(e.student_id) AS enrolled_students
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name
ORDER BY enrolled_students DESC;

-- ═══════════════════════════════════════════════════════════
-- SECTION 9: Comprehensive Reports
-- ═══════════════════════════════════════════════════════════

-- 9.1 — تقرير أداء الطالب (Student + Course + Avg)
SELECT
    s.student_id,
    s.full_name          AS student_name,
    c.course_name,
    ROUND(AVG(a.score)::numeric, 2) AS average_score
FROM assessments a
INNER JOIN students s ON a.student_id = s.student_id
INNER JOIN courses  c ON a.course_id  = c.course_id
GROUP BY s.student_id, s.full_name, c.course_id, c.course_name
ORDER BY average_score DESC;

-- 9.2 — تقرير أداء المدرسين
SELECT
    i.full_name          AS instructor_name,
    c.course_name,
    ROUND(AVG(a.score)::numeric, 2) AS average_score
FROM assessments a
INNER JOIN courses     c ON a.course_id    = c.course_id
INNER JOIN instructors i ON c.instructor_id = i.instructor_id
GROUP BY i.instructor_id, i.full_name, c.course_id, c.course_name
ORDER BY average_score DESC;

-- ═══════════════════════════════════════════════════════════
-- SECTION 10: ML-Ready Dataset (الأهم!)
-- ═══════════════════════════════════════════════════════════

SELECT
    s.student_id,
    s.full_name       AS student_name,
    s.city,
    COUNT(DISTINCT e.course_id) AS courses_count,
    COUNT(a.assessment_id)      AS assessments_count,
    ROUND(AVG(a.score)::numeric, 2) AS average_score,
    MAX(a.score)                AS highest_score,
    MIN(a.score)                AS lowest_score
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
LEFT JOIN assessments a ON s.student_id = a.student_id
GROUP BY s.student_id, s.full_name, s.city
ORDER BY average_score DESC;