-- ============================================================
-- JOINs — INNER JOIN, LEFT JOIN, Multi-Table
-- ============================================================

-- Q1: Students with their enrolled course IDs (INNER JOIN)
SELECT
    s.student_id,
    s.full_name AS student_name,
    e.course_id
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
ORDER BY s.student_id;

-- Q2: Students with course names (3-table JOIN)
SELECT
    s.student_id,
    s.full_name  AS student_name,
    c.course_name
FROM students s
INNER JOIN enrollments e ON s.student_id = e.student_id
INNER JOIN courses     c ON e.course_id  = c.course_id
ORDER BY s.student_id, c.course_name;

-- Q3: Students + Courses + Instructors (4-table JOIN)
SELECT
    s.full_name  AS student_name,
    c.course_name,
    i.full_name  AS instructor_name
FROM students s
INNER JOIN enrollments e ON s.student_id  = e.student_id
INNER JOIN courses     c ON e.course_id   = c.course_id
INNER JOIN instructors i ON c.instructor_id = i.instructor_id
ORDER BY student_name;

-- Q4: ALL students + their enrollments (LEFT JOIN)
SELECT
    s.student_id,
    s.full_name,
    e.course_id
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
ORDER BY s.student_id;

-- Q5: Students NOT enrolled in any course (LEFT JOIN + IS NULL)
SELECT
    s.student_id,
    s.full_name
FROM students s
LEFT JOIN enrollments e ON s.student_id = e.student_id
WHERE e.student_id IS NULL;

-- Q6: Number of students per course (LEFT JOIN keeps empty courses)
SELECT
    c.course_name,
    COUNT(e.student_id) AS enrolled_students
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name
ORDER BY enrolled_students DESC;
