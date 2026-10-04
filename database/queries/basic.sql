-- ============================================================
-- Basic Queries — SELECT, WHERE, ORDER BY
-- ============================================================

-- Q1: All students
SELECT student_id, full_name, city
FROM students
ORDER BY student_id;

-- Q2: Students from Sanaa
SELECT student_id, full_name, city
FROM students
WHERE city = 'Sanaa';

-- Q3: Students from Sanaa OR Dhamar
SELECT student_id, full_name, city
FROM students
WHERE city IN ('Sanaa', 'Dhamar')
ORDER BY city, full_name;

-- Q4: Students NOT from Sanaa
SELECT student_id, full_name, city
FROM students
WHERE NOT city = 'Sanaa';

-- Q5: High scores (>= 90)
SELECT student_id, course_id, assessment_type, score
FROM assessments
WHERE score >= 90
ORDER BY score DESC;

-- Q6: Students sorted by city then name
SELECT student_id, full_name, city
FROM students
ORDER BY city ASC, full_name ASC;
