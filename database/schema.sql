-- ============================================================
-- University Training Database — Schema
-- ============================================================
-- SQLite-compatible DDL
-- Enforces: PK, FK, NOT NULL, UNIQUE, CHECK
-- ============================================================

-- Enable foreign key enforcement
PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Table: instructors
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS instructors (
    instructor_id  INTEGER       PRIMARY KEY,
    full_name      TEXT          NOT NULL,
    department     TEXT          NOT NULL,
    email          TEXT          UNIQUE
);

-- ------------------------------------------------------------
-- Table: students
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    student_id     INTEGER       PRIMARY KEY,
    full_name      TEXT          NOT NULL,
    gender         TEXT          CHECK (gender IN ('Male', 'Female')),
    date_of_birth  DATE,
    city           TEXT
);

-- ------------------------------------------------------------
-- Table: courses
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS courses (
    course_id      INTEGER       PRIMARY KEY,
    course_name    TEXT          NOT NULL,
    credit_hours   INTEGER       NOT NULL CHECK (credit_hours > 0),
    instructor_id  INTEGER,
    FOREIGN KEY (instructor_id)
        REFERENCES instructors(instructor_id)
        ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Table: enrollments (many-to-many bridge)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id   INTEGER      PRIMARY KEY,
    student_id      INTEGER      NOT NULL,
    course_id       INTEGER      NOT NULL,
    enrollment_date DATE         NOT NULL,
    semester        TEXT         NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE,
    UNIQUE (student_id, course_id, semester)
);

-- ------------------------------------------------------------
-- Table: assessments
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id    INTEGER     PRIMARY KEY,
    student_id       INTEGER     NOT NULL,
    course_id        INTEGER     NOT NULL,
    assessment_type  TEXT        NOT NULL
                                 CHECK (assessment_type IN ('Midterm', 'Final', 'Quiz', 'Project')),
    score            REAL        NOT NULL CHECK (score >= 0 AND score <= 100),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Indexes for common queries
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_enrollments_student   ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course    ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_assessments_student   ON assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_assessments_course    ON assessments(course_id);
