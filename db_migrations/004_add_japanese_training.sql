-- Migration 004: Japanese Language Training Platform
-- Tables for N5-N1 JLPT preparation courses

-- Japanese Courses (N5-N1 levels)
CREATE TABLE japanese_courses (
    course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(10) NOT NULL, -- 'N5', 'N4', 'N3', 'N2', 'N1'
    course_name VARCHAR(255) NOT NULL,
    jlpt_level_num INTEGER NOT NULL, -- 5, 4, 3, 2, 1
    duration_weeks INTEGER NOT NULL,
    price_self_paced DECIMAL(10,2) NOT NULL,
    price_interactive DECIMAL(10,2),
    price_premium DECIMAL(10,2),
    price_vr DECIMAL(10,2),
    description TEXT,
    prerequisites JSONB,
    learning_objectives JSONB,
    vocabulary_count INTEGER,
    kanji_count INTEGER,
    grammar_patterns INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lessons within courses
CREATE TABLE japanese_lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES japanese_courses(course_id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    lesson_number INTEGER NOT NULL,
    lesson_title VARCHAR(255) NOT NULL,
    lesson_type VARCHAR(50) NOT NULL, -- 'video', 'reading', 'audio', 'practice', 'quiz'
    content_url VARCHAR(500),
    duration_minutes INTEGER,
    vocabulary_introduced JSONB,
    kanji_introduced JSONB,
    grammar_points JSONB,
    difficulty_level VARCHAR(20),
    is_required BOOLEAN DEFAULT TRUE,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vocabulary Database
CREATE TABLE japanese_vocabulary (
    vocab_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_hiragana VARCHAR(100) NOT NULL,
    word_kanji VARCHAR(100),
    word_romaji VARCHAR(100),
    english_meaning TEXT NOT NULL,
    part_of_speech VARCHAR(50),
    jlpt_level VARCHAR(10),
    example_sentence_japanese TEXT,
    example_sentence_english TEXT,
    audio_url VARCHAR(500),
    image_url VARCHAR(500),
    frequency_rank INTEGER,
    related_words JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kanji Database
CREATE TABLE japanese_kanji (
    kanji_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character CHAR(1) NOT NULL UNIQUE,
    kunyomi VARCHAR(100),
    onyomi VARCHAR(100),
    english_meaning TEXT NOT NULL,
    stroke_count INTEGER NOT NULL,
    jlpt_level VARCHAR(10),
    radical VARCHAR(50),
    stroke_order_animation_url VARCHAR(500),
    example_words JSONB,
    mnemonic TEXT,
    frequency_rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grammar Patterns
CREATE TABLE japanese_grammar (
    grammar_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_structure TEXT NOT NULL,
    english_explanation TEXT NOT NULL,
    jlpt_level VARCHAR(10),
    formality_level VARCHAR(20),
    usage_notes TEXT,
    example_sentences JSONB,
    common_mistakes TEXT,
    related_patterns JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student Enrollments
CREATE TABLE japanese_enrollments (
    enrollment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    course_id UUID REFERENCES japanese_courses(course_id) ON DELETE CASCADE,
    delivery_mode VARCHAR(50) NOT NULL, -- 'self_paced', 'interactive', 'premium', 'vr'
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    current_week INTEGER DEFAULT 1,
    current_lesson_id UUID REFERENCES japanese_lessons(lesson_id),
    status VARCHAR(20) DEFAULT 'enrolled',
    final_exam_score DECIMAL(5,2),
    certificate_issued BOOLEAN DEFAULT FALSE
);

-- Lesson Progress Tracking
CREATE TABLE japanese_lesson_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES japanese_enrollments(enrollment_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES japanese_lessons(lesson_id) ON DELETE CASCADE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    time_spent_minutes INTEGER DEFAULT 0,
    quiz_attempts INTEGER DEFAULT 0,
    quiz_best_score DECIMAL(5,2),
    mastery_level VARCHAR(20),
    notes TEXT
);

-- Vocabulary Progress (SRS - Spaced Repetition System)
CREATE TABLE japanese_vocab_progress (
    vocab_progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    vocab_id UUID REFERENCES japanese_vocabulary(vocab_id) ON DELETE CASCADE,
    times_reviewed INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_incorrect INTEGER DEFAULT 0,
    srs_level INTEGER DEFAULT 1,
    next_review_date TIMESTAMP,
    last_reviewed_at TIMESTAMP,
    is_mastered BOOLEAN DEFAULT FALSE,
    difficulty_rating INTEGER
);

-- Kanji Progress
CREATE TABLE japanese_kanji_progress (
    kanji_progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    kanji_id UUID REFERENCES japanese_kanji(kanji_id) ON DELETE CASCADE,
    recognition_level INTEGER DEFAULT 0,
    writing_level INTEGER DEFAULT 0,
    times_practiced INTEGER DEFAULT 0,
    last_practiced_at TIMESTAMP,
    is_mastered BOOLEAN DEFAULT FALSE
);

-- Quizzes
CREATE TABLE japanese_quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES japanese_lessons(lesson_id) ON DELETE CASCADE,
    quiz_title VARCHAR(255) NOT NULL,
    quiz_type VARCHAR(50) NOT NULL,
    time_limit_minutes INTEGER,
    passing_score DECIMAL(5,2) DEFAULT 70.00,
    questions JSONB NOT NULL,
    difficulty VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quiz Attempts
CREATE TABLE japanese_quiz_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES japanese_enrollments(enrollment_id) ON DELETE CASCADE,
    quiz_id UUID REFERENCES japanese_quizzes(quiz_id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    score DECIMAL(5,2),
    answers JSONB,
    feedback JSONB,
    time_taken_minutes INTEGER,
    passed BOOLEAN DEFAULT FALSE,
    attempt_number INTEGER DEFAULT 1
);

-- JLPT Mock Tests
CREATE TABLE japanese_mock_tests (
    mock_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jlpt_level VARCHAR(10) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    sections JSONB NOT NULL,
    total_questions INTEGER NOT NULL,
    time_limit_minutes INTEGER NOT NULL,
    passing_score DECIMAL(5,2) DEFAULT 70.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Mock Test Attempts
CREATE TABLE japanese_mock_test_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    mock_test_id UUID REFERENCES japanese_mock_tests(mock_test_id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    vocabulary_score DECIMAL(5,2),
    grammar_score DECIMAL(5,2),
    reading_score DECIMAL(5,2),
    listening_score DECIMAL(5,2),
    total_score DECIMAL(5,2),
    passed BOOLEAN DEFAULT FALSE,
    detailed_results JSONB,
    weak_areas JSONB
);

-- Speaking Practice (AI Tutor Integration)
CREATE TABLE japanese_speaking_practice (
    practice_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES japanese_lessons(lesson_id),
    prompt_text TEXT NOT NULL,
    audio_recording_url VARCHAR(500),
    transcript_romaji TEXT,
    transcript_hiragana TEXT,
    ai_pronunciation_score DECIMAL(5,2),
    ai_feedback TEXT,
    ai_pronunciation_details JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Writing Practice
CREATE TABLE japanese_writing_practice (
    writing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES japanese_lessons(lesson_id),
    prompt_text TEXT NOT NULL,
    student_writing TEXT NOT NULL,
    writing_type VARCHAR(50),
    ai_grammar_check JSONB,
    ai_feedback TEXT,
    teacher_feedback TEXT,
    score DECIMAL(5,2),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

-- Certificates
CREATE TABLE japanese_certificates (
    certificate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    course_id UUID REFERENCES japanese_courses(course_id) ON DELETE CASCADE,
    jlpt_level VARCHAR(10) NOT NULL,
    certificate_type VARCHAR(100) NOT NULL,
    final_score DECIMAL(5,2),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    certificate_url VARCHAR(500),
    certificate_image_url VARCHAR(500),
    verification_code VARCHAR(50) UNIQUE NOT NULL,
    linkedin_share_url VARCHAR(500)
);

-- Study Streaks (Gamification)
CREATE TABLE japanese_study_streaks (
    streak_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_study_date DATE,
    total_study_days INTEGER DEFAULT 0,
    total_study_minutes INTEGER DEFAULT 0,
    streak_broken_count INTEGER DEFAULT 0
);

-- Achievements / Badges
CREATE TABLE japanese_achievements (
    achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_type VARCHAR(100) NOT NULL,
    achievement_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    xp_awarded INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX idx_japanese_courses_level ON japanese_courses(level);
CREATE INDEX idx_japanese_lessons_course ON japanese_lessons(course_id);
CREATE INDEX idx_japanese_vocab_level ON japanese_vocabulary(jlpt_level);
CREATE INDEX idx_japanese_kanji_level ON japanese_kanji(jlpt_level);
CREATE INDEX idx_japanese_enrollments_user ON japanese_enrollments(user_id);
CREATE INDEX idx_japanese_vocab_progress_user ON japanese_vocab_progress(user_id);
CREATE INDEX idx_japanese_vocab_progress_next_review ON japanese_vocab_progress(next_review_date);
