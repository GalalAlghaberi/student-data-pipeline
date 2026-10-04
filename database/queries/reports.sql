-- ============================================================
-- Analytical Reports — Data Engineering Perspective
-- ============================================================

-- Report 1: Student Performance (Student + Course + Average Score)
SELECT
    s.student_id,
    s.full_name          AS student_name,
    c.course_name,
    ROUND(AVG(a.score), 2) AS average_score
FROM assessments a
INNER JOIN students s ON a.student_id = s.student_id
INNER JOIN courses  c ON a.course_id  = c.course_id
GROUP BY s.student_id, s.full_name, c.course_id, c.course_name
ORDER BY average_score DESC;

-- Report 2: Instructor Performance
SELECT
    i.full_name          AS instructor_name,
    c.course_name,
    ROUND(AVG(a.score), 2) AS average_score
FROM assessments a
INNER JOIN courses     c ON a.course_id    = c.course_id
INNER JOIN instructors i ON c.instructor_id = i.instructor_id
GROUP BY i.instructor_id, i.full_name, c.course_id, c.course_name
ORDER BY average_score DESC;

-- Report 3: ML-Ready Feature Table
--   This is the final output used to build ML datasets.
SELECT
    s.student_id,
    s.full_name       AS student_name,
    s.city,
    COUNT(DISTINCT e.course_id) AS courses_count,
    COUNT(a.assessment_id)      AS assessments_count,
    ROUND(AVG(a.score), 2)      AS average_score,
    MAX(a.score)                AS highest_score,
    MIN(a.score)                AS lowest_score
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
LEFT JOIN assessments a ON s.student_id = a.student_id
GROUP BY s.student_id, s.full_name, s.city
ORDER BY average_score DESC;
