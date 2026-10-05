-- ============================================================
-- First Advanced Query — Student Ranking
-- ============================================================

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