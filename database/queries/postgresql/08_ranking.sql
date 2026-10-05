-- ============================================================
-- Session 5 — Ranking Functions (PostgreSQL)
-- University Training Database
-- ============================================================

-- ═══════════════════════════════════════════════════════════
-- PART 1: مقارنة الدوال الثلاث (الأهم)
-- ═══════════════════════════════════════════════════════════

-- Q1: عرض ROW_NUMBER و RANK و DENSE_RANK معًا
SELECT
    assessment_id,
    student_id,
    score,
    ROW_NUMBER()  OVER (ORDER BY score DESC) AS row_num,
    RANK()        OVER (ORDER BY score DESC) AS rank_val,
    DENSE_RANK()  OVER (ORDER BY score DESC) AS dense_rank_val
FROM assessments
ORDER BY score DESC;

-- ═══════════════════════════════════════════════════════════
-- PART 2: ROW_NUMBER
-- ═══════════════════════════════════════════════════════════

-- Q2: ترقيم كل تقييم
SELECT
    student_id,
    score,
    ROW_NUMBER() OVER (ORDER BY score DESC) AS row_num
FROM assessments
ORDER BY row_num;

-- Q3: ترقيم داخل كل طالب
SELECT
    student_id,
    assessment_id,
    score,
    ROW_NUMBER() OVER (
        PARTITION BY student_id
        ORDER BY score DESC
    ) AS score_rank_within_student
FROM assessments
ORDER BY student_id, score_rank_within_student;

-- ═══════════════════════════════════════════════════════════
-- PART 3: RANK
-- ═══════════════════════════════════════════════════════════

-- Q4: ترتيب الطلاب بمتوسطاتهم
WITH student_avg AS (
    SELECT
        student_id,
        ROUND(AVG(score)::numeric, 2) AS average_score
    FROM assessments
    GROUP BY student_id
)
SELECT
    student_id,
    average_score,
    RANK() OVER (ORDER BY average_score DESC) AS student_rank
FROM student_avg
ORDER BY student_rank;

-- Q5: ترتيب الطلاب داخل مدينتهم ⭐ (الأهم)
WITH student_metrics AS (
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
    RANK() OVER (ORDER BY average_score DESC) AS university_rank,
    RANK() OVER (PARTITION BY city ORDER BY average_score DESC) AS city_rank
FROM student_metrics
ORDER BY university_rank;

-- ═══════════════════════════════════════════════════════════
-- PART 4: DENSE_RANK
-- ═══════════════════════════════════════════════════════════

-- Q6: الفرق بين RANK و DENSE_RANK
SELECT
    score,
    RANK()       OVER (ORDER BY score DESC) AS rank_gap,
    DENSE_RANK() OVER (ORDER BY score DESC) AS rank_dense
FROM assessments
ORDER BY score DESC
LIMIT 10;

-- ═══════════════════════════════════════════════════════════
-- PART 5: Top-N per Group
-- ═══════════════════════════════════════════════════════════

-- Q7: أفضل تقييم لكل طالب
WITH ranked_scores AS (
    SELECT
        student_id,
        assessment_id,
        course_id,
        score,
        ROW_NUMBER() OVER (
            PARTITION BY student_id
            ORDER BY score DESC
        ) AS rn
    FROM assessments
)
SELECT
    student_id,
    assessment_id,
    course_id,
    score
FROM ranked_scores
WHERE rn = 1
ORDER BY student_id;

-- Q8: أفضل تقييمين لكل طالب
WITH ranked_scores AS (
    SELECT
        student_id,
        assessment_id,
        course_id,
        score,
        ROW_NUMBER() OVER (
            PARTITION BY student_id
            ORDER BY score DESC
        ) AS rn
    FROM assessments
)
SELECT
    student_id,
    assessment_id,
    course_id,
    score,
    rn AS position
FROM ranked_scores
WHERE rn <= 2
ORDER BY student_id, rn;

-- ═══════════════════════════════════════════════════════════
-- PART 6: Top 3 Students
-- ═══════════════════════════════════════════════════════════

-- Q9: أفضل 3 طلاب في الجامعة
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
        student_id,
        full_name,
        city,
        average_score,
        RANK() OVER (ORDER BY average_score DESC) AS student_rank
    FROM student_avg
)
SELECT *
FROM ranked
WHERE student_rank <= 3
ORDER BY student_rank;

-- ═══════════════════════════════════════════════════════════
-- PART 7: قائمة الشرف
-- ═══════════════════════════════════════════════════════════

-- Q10: قائمة شرف كاملة مع التصنيف
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
        RANK()       OVER (ORDER BY average_score DESC) AS university_rank,
        DENSE_RANK() OVER (ORDER BY average_score DESC) AS dense_rank
    FROM student_avg
)
SELECT
    university_rank,
    student_id,
    full_name,
    city,
    average_score,
    CASE
        WHEN university_rank = 1 THEN '🥇 Gold'
        WHEN university_rank = 2 THEN '🥈 Silver'
        WHEN university_rank = 3 THEN '🥉 Bronze'
        WHEN average_score >= 85 THEN '⭐ Honor'
        WHEN average_score >= 75 THEN '✅ Good'
        ELSE '📚 Needs Improvement'
    END AS achievement
FROM ranked
ORDER BY university_rank;