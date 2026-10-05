-- ============================================================
-- Session 2 — Subqueries (PostgreSQL)
-- University Training Database
-- ============================================================

-- Q1: الطلاب الذين حصلوا على 90 أو أكثر
SELECT DISTINCT
    s.student_id,
    s.full_name,
    s.city
FROM students s
WHERE s.student_id IN (
    SELECT student_id
    FROM assessments
    WHERE score >= 90
)
ORDER BY s.student_id;

-- Q2: الطلاب الذين تفوقوا على متوسط الجامعة
SELECT
    s.student_id,
    s.full_name,
    ROUND(AVG(a.score)::numeric, 2) AS student_avg
FROM students s
JOIN assessments a ON s.student_id = a.student_id
GROUP BY s.student_id, s.full_name
HAVING AVG(a.score) > (
    SELECT AVG(score) FROM assessments
)
ORDER BY student_avg DESC;

-- Q3: صاحب أعلى درجة في الجامعة
SELECT
    s.student_id,
    s.full_name,
    a.score,
    a.course_id,
    a.assessment_type
FROM students s
JOIN assessments a ON s.student_id = a.student_id
WHERE a.score = (
    SELECT MAX(score) FROM assessments
);

-- Q4: الطلاب الذين لم يحصلوا على 95+
SELECT
    s.student_id,
    s.full_name
FROM students s
WHERE s.student_id NOT IN (
    SELECT DISTINCT student_id
    FROM assessments
    WHERE score >= 95
)
ORDER BY s.student_id;

-- Q5: EXISTS — الطلاب المسجلون في مقرر واحد على الأقل
SELECT
    s.student_id,
    s.full_name
FROM students s
WHERE EXISTS (
    SELECT 1
    FROM enrollments e
    WHERE e.student_id = s.student_id
)
ORDER BY s.student_id;

-- Q6: Subquery في SELECT — متوسط المقرر بجانب كل تقييم
SELECT
    a.assessment_id,
    a.student_id,
    a.course_id,
    a.score,
    (
        SELECT ROUND(AVG(score)::numeric, 2)
        FROM assessments
        WHERE course_id = a.course_id
    ) AS course_avg
FROM assessments a
ORDER BY a.course_id, a.score DESC;