-- ============================================================
-- Advanced SQL — Session 1
-- CASE Expression + Conditional Aggregation
-- ============================================================

-- Q1: تصنيف درجات كل تقييم
SELECT
    assessment_id,
    student_id,
    score,
    CASE
        WHEN score >= 90 THEN 'Excellent'
        WHEN score >= 80 THEN 'Very Good'
        WHEN score >= 70 THEN 'Good'
        WHEN score >= 60 THEN 'Pass'
        ELSE 'Weak'
    END AS performance_level
FROM assessments
ORDER BY score DESC;

-- Q2: تصنيف + حالة NULL
SELECT
    student_id,
    score,
    CASE
        WHEN score IS NULL THEN 'Missing'
        WHEN score >= 90 THEN 'Excellent'
        WHEN score >= 70 THEN 'Good'
        ELSE 'Weak'
    END AS score_status
FROM assessments;

-- Q3: Conditional Aggregation — إحصاء شرطي
SELECT
    COUNT(*) AS total_assessments,
    SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) AS excellent_count,
    SUM(CASE WHEN score >= 80 AND score < 90 THEN 1 ELSE 0 END) AS very_good_count,
    SUM(CASE WHEN score >= 70 AND score < 80 THEN 1 ELSE 0 END) AS good_count,
    SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) AS weak_count
FROM assessments;

-- Q4: النسب المئوية
SELECT
    COUNT(*) AS total,
    ROUND(100.0 * SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) / COUNT(*), 2) AS excellent_pct,
    ROUND(100.0 * SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) / COUNT(*), 2) AS weak_pct
FROM assessments;

-- Q5: Conditional Aggregation by Course
SELECT
    course_id,
    COUNT(*) AS total,
    SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) AS excellent,
    SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) AS weak
FROM assessments
GROUP BY course_id
ORDER BY course_id;
