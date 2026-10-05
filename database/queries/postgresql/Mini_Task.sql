-- ═══════════════════════════════════════════════════════════
-- Mini Task: Student Analytics Report
-- ═══════════════════════════════════════════════════════════

WITH student_metrics AS (
    SELECT
        s.student_id,
        s.full_name,
        s.city,
        COUNT(DISTINCT e.course_id) AS courses_count,
        ROUND(AVG(a.score)::numeric, 2) AS average_score,
        MAX(a.score) AS highest_score,
        MIN(a.score) AS lowest_score
    FROM students s
    LEFT JOIN enrollments e ON s.student_id = e.student_id
    LEFT JOIN assessments a ON s.student_id = a.student_id
    GROUP BY s.student_id, s.full_name, s.city
)
SELECT
    student_id,
    full_name       AS student_name,
    city,
    courses_count,
    average_score,
    highest_score,
    lowest_score
FROM student_metrics
WHERE average_score IS NOT NULL
ORDER BY average_score DESC;