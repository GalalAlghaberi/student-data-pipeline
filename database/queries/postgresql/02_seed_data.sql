-- Instructors
INSERT INTO instructors (instructor_id, full_name, department, email) VALUES
    (1, 'Dr. Ahmed Ali',     'Computer Science',        'ahmed@university.edu'),
    (2, 'Dr. Sara Mohammed', 'Information Technology',  'sara@university.edu'),
    (3, 'Dr. Khaled Hassan', 'Computer Science',        'khaled@university.edu'),
    (4, 'Dr. Mona Saleh',    'Information Systems',     'mona@university.edu');

-- Students
INSERT INTO students (student_id, full_name, gender, date_of_birth, city) VALUES
    (1001, 'Ahmed Ali',      'Male',   '2003-04-15', 'Sanaa'),
    (1002, 'Sara Mohammed',  'Female', '2004-01-20', 'Dhamar'),
    (1003, 'Khaled Hassan',  'Male',   '2002-11-10', 'Ibb'),
    (1004, 'Mona Saleh',     'Female', '2003-07-22', 'Taiz'),
    (1005, 'Omar Ahmed',     'Male',   '2004-09-01', 'Sanaa'),
    (1006, 'Huda Mohammed',  'Female', '2003-12-11', 'Dhamar'),
    (1007, 'Ali Hassan',     'Male',   '2002-05-18', 'Ibb'),
    (1008, 'Noor Saleh',     'Female', '2004-02-25', 'Sanaa');

-- Courses
INSERT INTO courses (course_id, course_name, credit_hours, instructor_id) VALUES
    (101, 'Python Programming',     3, 1),
    (102, 'Database Systems',       3, 2),
    (103, 'Data Structures',        3, 3),
    (104, 'Web Development',        3, 4),
    (105, 'Artificial Intelligence', 4, 1);

-- Enrollments
INSERT INTO enrollments (enrollment_id, student_id, course_id, enrollment_date, semester) VALUES
    ( 1, 1001, 101, '2026-01-10', 'Spring 2026'),
    ( 2, 1001, 102, '2026-01-10', 'Spring 2026'),
    ( 3, 1002, 101, '2026-01-10', 'Spring 2026'),
    ( 4, 1002, 105, '2026-01-10', 'Spring 2026'),
    ( 5, 1003, 103, '2026-01-11', 'Spring 2026'),
    ( 6, 1003, 102, '2026-01-11', 'Spring 2026'),
    ( 7, 1004, 104, '2026-01-11', 'Spring 2026'),
    ( 8, 1004, 105, '2026-01-11', 'Spring 2026'),
    ( 9, 1005, 101, '2026-01-12', 'Spring 2026'),
    (10, 1005, 102, '2026-01-12', 'Spring 2026'),
    (11, 1006, 103, '2026-01-12', 'Spring 2026'),
    (12, 1007, 104, '2026-01-13', 'Spring 2026'),
    (13, 1008, 105, '2026-01-13', 'Spring 2026');

-- Assessments
INSERT INTO assessments (assessment_id, student_id, course_id, assessment_type, score) VALUES
    ( 1, 1001, 101, 'Midterm', 82), ( 2, 1001, 101, 'Final',  90),
    ( 3, 1001, 102, 'Midterm', 76), ( 4, 1001, 102, 'Final',  84),
    ( 5, 1002, 101, 'Midterm', 95), ( 6, 1002, 101, 'Final',  92),
    ( 7, 1002, 105, 'Midterm', 88), ( 8, 1002, 105, 'Final',  94),
    ( 9, 1003, 103, 'Midterm', 70), (10, 1003, 103, 'Final',  78),
    (11, 1003, 102, 'Midterm', 75), (12, 1003, 102, 'Final',  73),
    (13, 1004, 104, 'Midterm', 89), (14, 1004, 104, 'Final',  91),
    (15, 1004, 105, 'Midterm', 80), (16, 1004, 105, 'Final',  85),
    (17, 1005, 101, 'Midterm', 65), (18, 1005, 101, 'Final',  72),
    (19, 1005, 102, 'Midterm', 68), (20, 1005, 102, 'Final',  70),
    (21, 1006, 103, 'Midterm', 92), (22, 1006, 103, 'Final',  95),
    (23, 1007, 104, 'Midterm', 74), (24, 1007, 104, 'Final',  79),
    (25, 1008, 105, 'Midterm', 96), (26, 1008, 105, 'Final',  98);