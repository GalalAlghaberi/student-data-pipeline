-- ============================================================
-- Session 3 — Common Table Expressions (CTEs)
-- PostgreSQL — University Training Database
-- ============================================================

-- Q1: CTE بسيط — متوسط كل طالب
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
)
SELECT *
FROM student_averages
ORDER BY average_score DESC;

-- Q2: CTE + WHERE — الطلاب المتفوقون (85+)
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
)
SELECT *
FROM student_averages
WHERE average_score >= 85
ORDER BY average_score DESC;

-- Q3: CTE + JOIN — إضافة أسماء الطلاب
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
)
SELECT
    s.student_id,
    s.full_name,
    s.city,
    sa.average_score
FROM students s
JOIN student_averages sa ON s.student_id = sa.student_id
ORDER BY sa.average_score DESC;

-- Q4: Multiple CTEs — متوسط + عدد المقررات
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
),
course_counts AS (
    SELECT
        student_id,
        COUNT(DISTINCT course_id) AS courses_count
    FROM enrollments
    GROUP BY student_id
)
SELECT
    s.student_id,
    s.full_name,
    s.city,
    COALESCE(sa.average_score, 0) AS average_score,
    COALESCE(cc.courses_count, 0) AS courses_count
FROM students s
LEFT JOIN student_averages sa ON s.student_id = sa.student_id
LEFT JOIN course_counts cc    ON s.student_id = cc.student_id
ORDER BY sa.average_score DESC NULLS LAST;

-- Q5: CTE + CASE — تصنيف الطلاب
WITH student_averages AS (
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
    CASE
        WHEN average_score >= 90 THEN 'Excellent'
        WHEN average_score >= 85 THEN 'Very Good'
        WHEN average_score >= 75 THEN 'Good'
        WHEN average_score >= 65 THEN 'Pass'
        ELSE 'Needs Improvement'
    END AS performance_level
FROM student_averages
ORDER BY average_score DESC;

-- Q6: Multiple CTEs — تقرير تحليلي متكامل
--   يتضمن: المتوسط + عدد المقررات + التصنيف
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
),
course_counts AS (
    SELECT
        student_id,
        COUNT(DISTINCT course_id) AS courses_count
    FROM enrollments
    GROUP BY student_id
),
student_metrics AS (
    SELECT
        s.student_id,
        s.full_name,
        s.city,
        sa.average_score,
        cc.courses_count
    FROM students s
    LEFT JOIN student_averages sa ON s.student_id = sa.student_id
    LEFT JOIN course_counts cc    ON s.student_id = cc.student_id
)
SELECT
    student_id,
    full_name,
    city,
    average_score,
    courses_count,
    CASE
        WHEN average_score >= 90 THEN 'Excellent'
        WHEN average_score >= 80 THEN 'Very Good'
        WHEN average_score >= 70 THEN 'Good'
        ELSE 'Needs Improvement'
    END AS performance_level
FROM student_metrics
ORDER BY average_score DESC NULLS LAST;

-- Q7: CTE + Aggregate على نتيجة CTE
--   متوسط الفصل الكلي مقابل متوسط كل طالب
WITH student_averages AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
)
SELECT
    student_id,
    average_score,
    (SELECT ROUND(AVG(average_score)::numeric, 2) FROM student_averages) AS class_average,
    ROUND((average_score - (SELECT AVG(average_score) FROM student_averages))::numeric, 2) AS diff_from_class
FROM student_averages
ORDER BY average_score DESC;