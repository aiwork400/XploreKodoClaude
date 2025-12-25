-- Migration 005: AI/ML Training Platform
-- Tables for AI/ML courses, projects, and certifications

-- AI/ML Courses
CREATE TABLE aiml_courses (
    course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_name VARCHAR(255) NOT NULL,
    level INTEGER NOT NULL, -- 1=Fundamentals, 2=Python DS, 3=ML Eng, 4=Specialization, 5=Capstone
    track VARCHAR(50), -- NULL for levels 1-3, 'computer_vision'/'nlp'/'rl'/'mlops' for level 4
    duration_weeks INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    prerequisites JSONB,
    syllabus_url VARCHAR(500),
    learning_objectives JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI/ML Lessons
CREATE TABLE aiml_lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES aiml_courses(course_id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    lesson_number INTEGER NOT NULL,
    lesson_title VARCHAR(255) NOT NULL,
    lesson_type VARCHAR(50) NOT NULL, -- 'video', 'reading', 'lab', 'quiz', 'project'
    content_url VARCHAR(500),
    jupyter_notebook_url VARCHAR(500),
    dataset_url VARCHAR(500),
    duration_minutes INTEGER,
    difficulty_level VARCHAR(20),
    topics JSONB,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI/ML Enrollments
CREATE TABLE aiml_enrollments (
    enrollment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    course_id UUID REFERENCES aiml_courses(course_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'enrolled', -- 'enrolled', 'active', 'completed', 'dropped'
    final_grade DECIMAL(5,2),
    certificate_issued BOOLEAN DEFAULT FALSE
);

-- Lesson Progress
CREATE TABLE aiml_lesson_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES aiml_enrollments(enrollment_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES aiml_lessons(lesson_id) ON DELETE CASCADE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent_minutes INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed'
    notes TEXT
);

-- Code Submissions
CREATE TABLE aiml_code_submissions (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES aiml_lessons(lesson_id) ON DELETE CASCADE,
    code_content TEXT NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    auto_grade_score DECIMAL(5,2),
    ai_feedback TEXT,
    test_results JSONB,
    passed BOOLEAN DEFAULT FALSE
);

-- AI/ML Projects
CREATE TABLE aiml_projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    course_id UUID REFERENCES aiml_courses(course_id) ON DELETE CASCADE,
    project_title VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) NOT NULL, -- 'capstone', 'course_project', 'portfolio'
    description TEXT,
    github_url VARCHAR(500),
    demo_url VARCHAR(500),
    technologies_used JSONB,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grade DECIMAL(5,2),
    feedback TEXT,
    is_portfolio_featured BOOLEAN DEFAULT FALSE
);

-- Certificates
CREATE TABLE aiml_certificates (
    certificate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    course_id UUID REFERENCES aiml_courses(course_id),
    certificate_type VARCHAR(100) NOT NULL, -- 'AI Fundamentals', 'Python for DS', 'ML Engineer', etc.
    final_score DECIMAL(5,2),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    certificate_url VARCHAR(500),
    verification_code VARCHAR(50) UNIQUE NOT NULL,
    linkedin_share_url VARCHAR(500),
    is_industry_recognized BOOLEAN DEFAULT FALSE
);

-- Learning Paths
CREATE TABLE aiml_learning_paths (
    path_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_name VARCHAR(255) NOT NULL, -- 'AI Enthusiast', 'Data Analyst', 'ML Engineer', 'Full Stack AI'
    description TEXT,
    courses JSONB NOT NULL, -- Array of course_ids in sequence
    total_duration_weeks INTEGER NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    job_placement_guarantee BOOLEAN DEFAULT FALSE,
    guarantee_percentage INTEGER, -- 80 for ML Engineer path
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Path Enrollments
CREATE TABLE aiml_path_enrollments (
    path_enrollment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    path_id UUID REFERENCES aiml_learning_paths(path_id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_courses JSONB DEFAULT '[]', -- Array of completed course_ids
    current_course_id UUID REFERENCES aiml_courses(course_id),
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'active'
);

-- Leaderboard
CREATE TABLE aiml_leaderboard (
    leaderboard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    total_xp INTEGER DEFAULT 0,
    badges_earned JSONB DEFAULT '[]',
    projects_completed INTEGER DEFAULT 0,
    ranking INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Job Placements
CREATE TABLE aiml_job_placements (
    placement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    salary_jpy DECIMAL(12,2),
    placement_date DATE NOT NULL,
    placement_fee DECIMAL(10,2), -- 10% of first year salary
    visa_status VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_aiml_courses_level ON aiml_courses(level);
CREATE INDEX idx_aiml_courses_track ON aiml_courses(track);
CREATE INDEX idx_aiml_enrollments_user ON aiml_enrollments(user_id);
CREATE INDEX idx_aiml_enrollments_status ON aiml_enrollments(status);
CREATE INDEX idx_aiml_projects_user ON aiml_projects(user_id);
CREATE INDEX idx_aiml_projects_featured ON aiml_projects(is_portfolio_featured);
CREATE INDEX idx_aiml_leaderboard_ranking ON aiml_leaderboard(ranking);
CREATE INDEX idx_aiml_leaderboard_xp ON aiml_leaderboard(total_xp DESC);
