-- ============================================================
-- Aggregates — COUNT, AVG, MIN, MAX, SUM, GROUP BY, HAVING
-- ============================================================

-- Q1: Total number of students
SELECT COUNT(*) AS total_students
FROM students;

-- Q2: Overall average score
SELECT ROUND(AVG(score), 2) AS average_score
FROM assessments;

-- Q3: Highest and lowest scores
SELECT
    MAX(score) AS highest_score,
    MIN(score) AS lowest_score
FROM assessments;

-- Q4: Total of all scores
SELECT SUM(score) AS total_scores
FROM assessments;

-- Q5: Number of students per city
SELECT city, COUNT(*) AS student_count
FROM students
GROUP BY city
ORDER BY student_count DESC;

-- Q6: Average score per student
SELECT
    student_id,
    ROUND(AVG(score), 2) AS average_score
FROM assessments
GROUP BY student_id
ORDER BY average_score DESC;

-- Q7: Average score per course
SELECT
    course_id,
    ROUND(AVG(score), 2) AS average_score
FROM assessments
GROUP BY course_id
ORDER BY average_score DESC;

-- Q8: High-performing students (avg >= 85) — uses HAVING
SELECT
    student_id,
    ROUND(AVG(score), 2) AS average_score
FROM assessments
GROUP BY student_id
HAVING AVG(score) >= 85
ORDER BY average_score DESC;
