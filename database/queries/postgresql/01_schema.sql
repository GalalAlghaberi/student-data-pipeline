-- ============================================================
-- University Training Database — PostgreSQL Schema
-- ============================================================

-- Instructors
CREATE TABLE instructors (
    instructor_id  INTEGER      PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    department     VARCHAR(100) NOT NULL,
    email          VARCHAR(150) UNIQUE
);

-- Students
CREATE TABLE students (
    student_id     INTEGER      PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    gender         VARCHAR(20)  CHECK (gender IN ('Male', 'Female')),
    date_of_birth  DATE,
    city           VARCHAR(100)
);

-- Courses
CREATE TABLE courses (
    course_id      INTEGER      PRIMARY KEY,
    course_name    VARCHAR(150) NOT NULL,
    credit_hours   INTEGER      NOT NULL CHECK (credit_hours > 0),
    instructor_id  INTEGER,
    FOREIGN KEY (instructor_id)
        REFERENCES instructors(instructor_id)
        ON DELETE SET NULL
);

-- Enrollments
CREATE TABLE enrollments (
    enrollment_id   INTEGER      PRIMARY KEY,
    student_id      INTEGER      NOT NULL,
    course_id       INTEGER      NOT NULL,
    enrollment_date DATE         NOT NULL,
    semester        VARCHAR(50)  NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE,
    UNIQUE (student_id, course_id, semester)
);

-- Assessments
CREATE TABLE assessments (
    assessment_id    INTEGER      PRIMARY KEY,
    student_id       INTEGER      NOT NULL,
    course_id        INTEGER      NOT NULL,
    assessment_type  VARCHAR(50)  NOT NULL
                                  CHECK (assessment_type IN ('Midterm', 'Final', 'Quiz', 'Project')),
    score            DECIMAL(5,2) NOT NULL CHECK (score >= 0 AND score <= 100),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course  ON enrollments(course_id);
CREATE INDEX idx_assessments_student ON assessments(student_id);
CREATE INDEX idx_assessments_course  ON assessments(course_id);