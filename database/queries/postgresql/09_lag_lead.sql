-- ============================================================
-- Session 6 — LAG, LEAD, Running Totals (PostgreSQL)
-- University Training Database
-- ============================================================

-- ═══════════════════════════════════════════════════════════
-- PART 1: LAG — القيمة السابقة
-- ═══════════════════════════════════════════════════════════

-- Q1: الدرجة السابقة لكل تقييم
SELECT
    student_id,
    course_id,
    assessment_id,
    assessment_type,
    score,
    LAG(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS previous_score
FROM assessments
ORDER BY student_id, course_id, assessment_id;

-- Q2: الفرق بين الدرجة الحالية والسابقة (التطور)
SELECT
    student_id,
    course_id,
    assessment_type,
    assessment_id,
    score AS current_score,
    LAG(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS previous_score,
    score - LAG(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS score_change
FROM assessments
ORDER BY student_id, course_id, assessment_id;

-- Q3: تصنيف التطور (Improvement / Decline)
WITH progress AS (
    SELECT
        student_id,
        course_id,
        assessment_type,
        assessment_id,
        score,
        LAG(score) OVER (
            PARTITION BY student_id, course_id
            ORDER BY assessment_id
        ) AS previous_score
    FROM assessments
)
SELECT
    student_id,
    course_id,
    assessment_type,
    score AS current_score,
    previous_score,
    score - previous_score AS score_change,
    CASE
        WHEN previous_score IS NULL THEN 'First Assessment'
        WHEN score > previous_score THEN '📈 Improved'
        WHEN score < previous_score THEN '📉 Declined'
        ELSE '➡️ No Change'
    END AS progress_status
FROM progress
ORDER BY student_id, course_id, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 2: LEAD — القيمة التالية
-- ═══════════════════════════════════════════════════════════

-- Q4: الدرجة التالية لكل تقييم
SELECT
    student_id,
    course_id,
    assessment_id,
    assessment_type,
    score,
    LEAD(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS next_score
FROM assessments
ORDER BY student_id, course_id, assessment_id;

-- Q5: LAG و LEAD في استعلام واحد (نظرة شاملة)
SELECT
    student_id,
    course_id,
    assessment_type,
    assessment_id,
    score,
    LAG(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS previous,
    score AS current,
    LEAD(score) OVER (
        PARTITION BY student_id, course_id
        ORDER BY assessment_id
    ) AS next
FROM assessments
ORDER BY student_id, course_id, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 3: Running Total (المجموع التراكمي)
-- ═══════════════════════════════════════════════════════════

-- Q6: المجموع التراكمي لكل تقييم (على مستوى الجامعة)
SELECT
    assessment_id,
    student_id,
    score,
    SUM(score) OVER (ORDER BY assessment_id) AS running_total
FROM assessments
ORDER BY assessment_id;

-- Q7: المجموع التراكمي لكل طالب
SELECT
    student_id,
    assessment_id,
    score,
    SUM(score) OVER (
        PARTITION BY student_id
        ORDER BY assessment_id
    ) AS running_total
FROM assessments
ORDER BY student_id, assessment_id;

-- Q8: المجموع التراكمي مع الإطار الصريح
SELECT
    student_id,
    assessment_id,
    score,
    SUM(score) OVER (
        PARTITION BY student_id
        ORDER BY assessment_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM assessments
ORDER BY student_id, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 4: Running Average (المتوسط التراكمي)
-- ═══════════════════════════════════════════════════════════

-- Q9: المتوسط التراكمي لكل طالب
SELECT
    student_id,
    assessment_id,
    score,
    ROUND(AVG(score) OVER (
        PARTITION BY student_id
        ORDER BY assessment_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )::numeric, 2) AS running_avg
FROM assessments
ORDER BY student_id, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 5: تحليل متقدم — التطور الكامل
-- ═══════════════════════════════════════════════════════════

-- Q10: تقرير التطور لكل طالب ومقرر
WITH progress AS (
    SELECT
        s.full_name       AS student_name,
        c.course_name,
        a.assessment_id,
        a.assessment_type,
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
    score,
    previous_score,
    score - previous_score AS change,
    CASE
        WHEN previous_score IS NULL THEN '—'
        WHEN score > previous_score THEN '📈 +' || (score - previous_score)::text
        WHEN score < previous_score THEN '📉 ' || (score - previous_score)::text
        ELSE '➡️'
    END AS trend
FROM progress
WHERE previous_score IS NOT NULL
ORDER BY student_name, course_name, assessment_id;

-- ═══════════════════════════════════════════════════════════
-- PART 6: ملخص التطور لكل طالب
-- ═══════════════════════════════════════════════════════════

-- Q11: متوسط التطور لكل طالب
WITH progress AS (
    SELECT
        student_id,
        course_id,
        score,
        LAG(score) OVER (
            PARTITION BY student_id, course_id
            ORDER BY assessment_id
        ) AS previous_score
    FROM assessments
),
score_changes AS (
    SELECT
        student_id,
        score - previous_score AS change
    FROM progress
    WHERE previous_score IS NOT NULL
)
SELECT
    s.student_id,
    s.full_name,
    COUNT(sc.change) AS assessments_compared,
    ROUND(AVG(sc.change)::numeric, 2) AS avg_change,
    CASE
        WHEN AVG(sc.change) > 2 THEN '📈 Steady Improvement'
        WHEN AVG(sc.change) < -2 THEN '📉 Declining'
        ELSE '➡️ Stable'
    END AS trend_classification
FROM students s
JOIN score_changes sc ON s.student_id = sc.student_id
GROUP BY s.student_id, s.full_name
ORDER BY avg_change DESC;