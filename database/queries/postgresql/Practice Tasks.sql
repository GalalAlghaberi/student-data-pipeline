-- ═══════════════════════════════════════════════════════════
-- Unit 2 Practice Tasks — Solutions
-- ═══════════════════════════════════════════════════════════

-- Exercise 1: student_id, full_name, city لكل الطلاب
SELECT student_id, full_name, city
FROM students
ORDER BY student_id;

-- Exercise 2: الطلاب من صنعاء
SELECT student_id, full_name, city
FROM students
WHERE city = 'Sanaa';

-- Exercise 3: ترتيب أبجدي
SELECT student_id, full_name, city
FROM students
ORDER BY full_name ASC;

-- Exercise 4: أعلى 10 درجات
SELECT assessment_id, student_id, score
FROM assessments
ORDER BY score DESC
LIMIT 10;

-- Exercise 5: المتوسط العام
SELECT ROUND(AVG(score)::numeric, 2) AS avg_score
FROM assessments;

-- Exercise 6: عدد الطلاب في كل مدينة
SELECT city, COUNT(*) AS student_count
FROM students
GROUP BY city
ORDER BY student_count DESC;

-- Exercise 7: متوسط درجة > 80 لكل طالب
SELECT
    s.student_id,
    s.full_name,
    ROUND(AVG(a.score)::numeric, 2) AS average_score
FROM students s
JOIN assessments a ON s.student_id = a.student_id
GROUP BY s.student_id, s.full_name
HAVING AVG(a.score) > 80
ORDER BY average_score DESC;

-- Exercise 8: Student Name + Course Name (JOIN)
SELECT
    s.full_name AS student_name,
    c.course_name
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c     ON e.course_id  = c.course_id
ORDER BY s.full_name;

-- Exercise 9: عدد الطلاب في كل مقرر
SELECT
    c.course_name,
    COUNT(DISTINCT e.student_id) AS students_count
FROM courses c
LEFT JOIN enrollments e ON c.course_id = e.course_id
GROUP BY c.course_id, c.course_name
ORDER BY students_count DESC;

-- Exercise 10: المقرر الأعلى متوسطًا
SELECT
    c.course_name,
    ROUND(AVG(a.score)::numeric, 2) AS average_score
FROM courses c
JOIN assessments a ON c.course_id = a.course_id
GROUP BY c.course_id, c.course_name
ORDER BY average_score DESC
LIMIT 1;