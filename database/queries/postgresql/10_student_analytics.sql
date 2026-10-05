-- ============================================================
-- FINAL PROJECT — University Student Advanced Analytics
-- Unit 3 Comprehensive Report
-- PostgreSQL — University Training Database
-- ============================================================

-- ═══════════════════════════════════════════════════════════
-- REPORT 1: Top 3 Students
-- ═══════════════════════════════════════════════════════════

WITH student_avg AS (
    SELECT
        s.student_id,
        s.full_name,
        s.city,
        ROUND(AVG(a.score)::numeric, 2) AS average_score
    FROM students s
    JOIN assessments a ON s.student_id = a.student_id
    GROUP BY s.student_id, s.full_name, s.city
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY average_score DESC) AS student_rank
    FROM student_avg
)
SELECT
    student_rank,
    student_id,
    full_name,
    city,
    average_score
FROM ranked
WHERE student_rank <= 3
ORDER BY student_rank;

-- ═══════════════════════════════════════════════════════════
-- REPORT 2: Student Ranking (كل الطلاب)
-- ═══════════════════════════════════════════════════════════

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
    RANK()       OVER (ORDER BY average_score DESC) AS student_rank,
    DENSE_RANK() OVER (ORDER BY average_score DESC) AS dense_rank,
    student_id,
    full_name,
    city,
    average_score
FROM student_avg
ORDER BY student_rank;

-- ═══════════════════════════════════════════════════════════
-- REPORT 3: City Ranking (ترتيب داخل كل مدينة)
-- ═══════════════════════════════════════════════════════════

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
    city,
    RANK() OVER (PARTITION BY city ORDER BY average_score DESC) AS city_rank,
    student_id,
    full_name,
    average_score,
    RANK() OVER (ORDER BY average_score DESC) AS university_rank
FROM student_avg
ORDER BY city, city_rank;

-- ═══════════════════════════════════════════════════════════
-- REPORT 4: Course Ranking (ترتيب المقررات)
-- ═══════════════════════════════════════════════════════════

WITH course_avg AS (
    SELECT
        c.course_id,
        c.course_name,
        i.full_name AS instructor_name,
        ROUND(AVG(a.score)::numeric, 2) AS average_score,
        COUNT(a.assessment_id) AS assessment_count
    FROM courses c
    JOIN assessments a ON c.course_id = a.course_id
    JOIN instructors i ON c.instructor_id = i.instructor_id
    GROUP BY c.course_id, c.course_name, i.full_name
)
SELECT
    RANK() OVER (ORDER BY average_score DESC) AS course_rank,
    course_id,
    course_name,
    instructor_name,
    assessment_count,
    average_score
FROM course_avg
ORDER BY course_rank;

-- ═══════════════════════════════════════════════════════════
-- REPORT 5: Performance Classification
-- ═══════════════════════════════════════════════════════════

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
    CASE
        WHEN average_score >= 90 THEN 'Excellent'
        WHEN average_score >= 80 THEN 'Very Good'
        WHEN average_score >= 70 THEN 'Good'
        WHEN average_score >= 60 THEN 'Pass'
        ELSE 'Weak'
    END AS performance_level,
    CASE
        WHEN average_score >= 85 THEN 'Top Performer'
        WHEN average_score >= 75 THEN 'Average'
        ELSE 'Needs Improvement'
    END AS overall_status
FROM student_avg
ORDER BY average_score DESC;

-- ═══════════════════════════════════════════════════════════
-- REPORT 6: Progress Analysis (LAG)
-- ═══════════════════════════════════════════════════════════

WITH progress AS (
    SELECT
        s.full_name AS student_name,
        c.course_name,
        a.assessment_type,
        a.assessment_id,
        a.score,
        LAG(a.score) OVER (
            PARTITION BY a.student_id, a.course_id
            ORDER BY a.assessment_id
        ) AS previous_score
    FROM assessments a
    INNER JOIN students s ON a.student_id = s.student_id
    INNER JOIN courses  c ON a.course_id  = c.course_id
)
SELECT
    student_name,
    course_name,
    assessment_type,
    score AS current_score,
    previous_score,
    score - previous_score AS score_change,
    CASE
        WHEN previous_score IS NULL THEN 'First Assessment'
        WHEN score > previous_score THEN 'Improved'
        WHEN score < previous_score THEN 'Declined'
        ELSE 'No Change'
    END AS progress_status
FROM progress
WHERE previous_score IS NOT NULL
ORDER BY student_name, course_name;

-- ═══════════════════════════════════════════════════════════
-- REPORT 7: Running Score (SUM OVER)
-- ═══════════════════════════════════════════════════════════

SELECT
    s.full_name AS student_name,
    a.assessment_id,
    a.score,
    SUM(a.score) OVER (
        PARTITION BY a.student_id
        ORDER BY a.assessment_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    ROUND(AVG(a.score) OVER (
        PARTITION BY a.student_id
        ORDER BY a.assessment_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )::numeric, 2) AS running_average
FROM assessments a
INNER JOIN students s ON a.student_id = s.student_id
ORDER BY a.student_id, a.assessment_id;

-- ═══════════════════════════════════════════════════════════
-- REPORT 8: Average vs University Average
-- ═══════════════════════════════════════════════════════════

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
    ROUND(AVG(average_score) OVER ()::numeric, 2) AS university_avg,
    ROUND((average_score - AVG(average_score) OVER ())::numeric, 2) AS diff_from_avg,
    CASE
        WHEN average_score > AVG(average_score) OVER () THEN 'Above Average'
        WHEN average_score < AVG(average_score) OVER () THEN 'Below Average'
        ELSE 'At Average'
    END AS position
FROM student_avg
ORDER BY average_score DESC;

-- ═══════════════════════════════════════════════════════════
-- FINAL: Consolidated Analytics Dataset
--   يجمع كل المقاييس في جدول واحد
-- ═══════════════════════════════════════════════════════════

WITH student_avg AS (
    SELECT
        s.student_id,
        s.full_name AS student_name,
        s.city,
        ROUND(AVG(a.score)::numeric, 2) AS average_score,
        MAX(a.score) AS highest_score,
        MIN(a.score) AS lowest_score,
        COUNT(a.assessment_id) AS assessments_count
    FROM students s
    LEFT JOIN assessments a ON s.student_id = a.student_id
    GROUP BY s.student_id, s.full_name, s.city
),
course_counts AS (
    SELECT
        student_id,
        COUNT(DISTINCT course_id) AS courses_count
    FROM enrollments
    GROUP BY student_id
),
metrics AS (
    SELECT
        sa.student_id,
        sa.student_name,
        sa.city,
        sa.average_score,
        sa.highest_score,
        sa.lowest_score,
        sa.assessments_count,
        COALESCE(cc.courses_count, 0) AS courses_count,
        RANK() OVER (ORDER BY sa.average_score DESC) AS university_rank,
        RANK() OVER (PARTITION BY sa.city ORDER BY sa.average_score DESC) AS city_rank,
        ROUND(AVG(sa.average_score) OVER ()::numeric, 2) AS university_avg
    FROM student_avg sa
    LEFT JOIN course_counts cc ON sa.student_id = cc.student_id
)
SELECT
    student_id,
    student_name,
    city,
    courses_count,
    assessments_count,
    average_score,
    highest_score,
    lowest_score,
    university_rank,
    city_rank,
    ROUND((average_score - university_avg)::numeric, 2) AS diff_from_avg,
    CASE
        WHEN average_score >= 90 THEN 'Excellent'
        WHEN average_score >= 80 THEN 'Very Good'
        WHEN average_score >= 70 THEN 'Good'
        ELSE 'Needs Improvement'
    END AS performance_level
FROM metrics
ORDER BY university_rank;