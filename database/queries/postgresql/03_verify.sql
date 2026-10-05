SELECT 'instructors' AS table_name, COUNT(*) FROM instructors
UNION ALL SELECT 'students',    COUNT(*) FROM students
UNION ALL SELECT 'courses',     COUNT(*) FROM courses
UNION ALL SELECT 'enrollments', COUNT(*) FROM enrollments
UNION ALL SELECT 'assessments', COUNT(*) FROM assessments;