-- ============================================================
-- Session 4 — Window Functions (PostgreSQL)
-- University Training Database
-- ============================================================

-- ═══════════════════════════════════════════════════════════
-- PART 1: الفرق بين GROUP BY و OVER
-- ═══════════════════════════════════════════════════════════

-- Q1: GROUP BY — يقلّص الصفوف
SELECT
    student_id,
    ROUND(AVG(score)::numeric, 2) AS student_avg
FROM assessments
GROUP BY student_id
ORDER BY student_id;

-- Q2: Window Function — يحتفظ بالصفوف
SELECT
    student_id,
    score,
    ROUND(AVG(score) OVER (PARTITION BY student_id)::numeric, 2) AS student_avg
FROM assessments
ORDER BY student_id, score;

-- ═══════════════════════════════════════════════════════════
-- PART 2: PARTITION BY
-- ═══════════════════════════════════════════════════════════

-- Q3: متوسط الطالب بجانب كل تقييم
SELECT
    assessment_id,
    student_id,
    course_id,
    score,
    ROUND(AVG(score) OVER (PARTITION BY student_id)::numeric, 2) AS student_avg,
    ROUND((score - AVG(score) OVER (PARTITION BY student_id))::numeric, 2) AS diff_from_student_avg
FROM assessments
ORDER BY student_id, score DESC;

-- Q4: متوسط المقرر بجانب كل تقييم
SELECT
    assessment_id,
    course_id,
    student_id,
    score,
    ROUND(AVG(score) OVER (PARTITION BY course_id)::numeric, 2) AS course_avg,
    ROUND((score - AVG(score) OVER (PARTITION BY course_id))::numeric, 2) AS diff_from_course_avg
FROM assessments
ORDER BY course_id, score DESC;

-- ═══════════════════════════════════════════════════════════
-- PART 3: المتوسط الجامعي (بدون PARTITION)
-- ═══════════════════════════════════════════════════════════

-- Q5: المتوسط الجامعي بجانب كل تقييم
SELECT
    assessment_id,
    student_id,
    score,
    ROUND(AVG(score) OVER ()::numeric, 2) AS university_avg,
    ROUND((score - AVG(score) OVER ())::numeric, 2) AS diff_from_university
FROM assessments
ORDER BY score DESC;

-- ═══════════════════════════════════════════════════════════
-- PART 4: مقارنة طالب بمتوسطه ومتوسط الجامعة
-- ═══════════════════════════════════════════════════════════

-- Q6: ثلاث مستويات في صف واحد
SELECT
    assessment_id,
    student_id,
    course_id,
    score,
    ROUND(AVG(score) OVER (PARTITION BY student_id)::numeric, 2) AS student_avg,
    ROUND(AVG(score) OVER (PARTITION BY course_id)::numeric, 2)  AS course_avg,
    ROUND(AVG(score) OVER ()::numeric, 2)                         AS university_avg
FROM assessments
ORDER BY student_id, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 5: Window Functions الأخرى
-- ═══════════════════════════════════════════════════════════

-- Q7: MAX / MIN / COUNT مع OVER
SELECT
    assessment_id,
    student_id,
    score,
    MAX(score) OVER (PARTITION BY student_id) AS student_max,
    MIN(score) OVER (PARTITION BY student_id) AS student_min,
    COUNT(*)   OVER (PARTITION BY student_id) AS student_assessments
FROM assessments
ORDER BY student_id, score DESC;

-- Q8: SUM مع OVER
SELECT
    assessment_id,
    student_id,
    score,
    SUM(score) OVER (PARTITION BY student_id) AS student_total
FROM assessments
ORDER BY student_id;

-- ═══════════════════════════════════════════════════════════
-- PART 6: تقرير تحليلي كامل
-- ═══════════════════════════════════════════════════════════

-- Q9: أداء كل تقييم مقارنة بمتوسط الطالب والمقرر والجامعة
SELECT
    a.assessment_id,
    s.full_name AS student_name,
    c.course_name,
    a.score,
    ROUND(AVG(a.score) OVER (PARTITION BY a.student_id)::numeric, 2) AS student_avg,
    ROUND(AVG(a.score) OVER (PARTITION BY a.course_id)::numeric, 2)  AS course_avg,
    ROUND(AVG(a.score) OVER ()::numeric, 2)                          AS university_avg,
    CASE
        WHEN a.score > AVG(a.score) OVER (PARTITION BY a.student_id) THEN 'Above Student Avg'
        WHEN a.score < AVG(a.score) OVER (PARTITION BY a.student_id) THEN 'Below Student Avg'
        ELSE 'At Student Avg'
    END AS student_position
FROM assessments a
INNER JOIN students s ON a.student_id = s.student_id
INNER JOIN courses  c ON a.course_id  = c.course_id
ORDER BY a.student_id, a.score DESC;