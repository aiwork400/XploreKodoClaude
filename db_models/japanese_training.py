"""
Japanese Language Training Database Models
N5-N1 JLPT preparation courses
"""
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, Text, TIMESTAMP, ForeignKey, Date, CHAR
from config.uuid_type import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from config.database import Base


class JapaneseCourseDB(Base):
    __tablename__ = "japanese_courses"
    
    course_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(10), nullable=False)
    course_name = Column(String(255), nullable=False)
    jlpt_level_num = Column(Integer, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    price_self_paced = Column(DECIMAL(10, 2), nullable=False)
    price_interactive = Column(DECIMAL(10, 2))
    price_premium = Column(DECIMAL(10, 2))
    price_vr = Column(DECIMAL(10, 2))
    description = Column(Text)
    prerequisites = Column(JSONB)
    learning_objectives = Column(JSONB)
    vocabulary_count = Column(Integer)
    kanji_count = Column(Integer)
    grammar_patterns = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class JapaneseLessonDB(Base):
    __tablename__ = "japanese_lessons"
    
    lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("japanese_courses.course_id", ondelete="CASCADE"))
    week_number = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    lesson_title = Column(String(255), nullable=False)
    lesson_type = Column(String(50), nullable=False)
    content_url = Column(String(500))
    duration_minutes = Column(Integer)
    vocabulary_introduced = Column(JSONB)
    kanji_introduced = Column(JSONB)
    grammar_points = Column(JSONB)
    difficulty_level = Column(String(20))
    is_required = Column(Boolean, default=True)
    sort_order = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseVocabularyDB(Base):
    __tablename__ = "japanese_vocabulary"
    
    vocab_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_hiragana = Column(String(100), nullable=False)
    word_kanji = Column(String(100))
    word_romaji = Column(String(100))
    english_meaning = Column(Text, nullable=False)
    part_of_speech = Column(String(50))
    jlpt_level = Column(String(10))
    example_sentence_japanese = Column(Text)
    example_sentence_english = Column(Text)
    audio_url = Column(String(500))
    image_url = Column(String(500))
    frequency_rank = Column(Integer)
    related_words = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseKanjiDB(Base):
    __tablename__ = "japanese_kanji"
    
    kanji_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    character = Column(CHAR(1), nullable=False, unique=True)
    kunyomi = Column(String(100))
    onyomi = Column(String(100))
    english_meaning = Column(Text, nullable=False)
    stroke_count = Column(Integer, nullable=False)
    jlpt_level = Column(String(10))
    radical = Column(String(50))
    stroke_order_animation_url = Column(String(500))
    example_words = Column(JSONB)
    mnemonic = Column(Text)
    frequency_rank = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseGrammarDB(Base):
    __tablename__ = "japanese_grammar"
    
    grammar_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_name = Column(String(255), nullable=False)
    pattern_structure = Column(Text, nullable=False)
    english_explanation = Column(Text, nullable=False)
    jlpt_level = Column(String(10))
    formality_level = Column(String(20))
    usage_notes = Column(Text)
    example_sentences = Column(JSONB)
    common_mistakes = Column(Text)
    related_patterns = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseEnrollmentDB(Base):
    __tablename__ = "japanese_enrollments"
    
    enrollment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("japanese_courses.course_id", ondelete="CASCADE"))
    delivery_mode = Column(String(50), nullable=False)
    enrolled_at = Column(TIMESTAMP, server_default=func.now())
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    progress_percentage = Column(DECIMAL(5, 2), default=0.00)
    current_week = Column(Integer, default=1)
    current_lesson_id = Column(UUID(as_uuid=True), ForeignKey("japanese_lessons.lesson_id"))
    status = Column(String(20), default="enrolled")
    final_exam_score = Column(DECIMAL(5, 2))
    certificate_issued = Column(Boolean, default=False)


class JapaneseLessonProgressDB(Base):
    __tablename__ = "japanese_lesson_progress"
    
    progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("japanese_enrollments.enrollment_id", ondelete="CASCADE"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("japanese_lessons.lesson_id", ondelete="CASCADE"))
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    time_spent_minutes = Column(Integer, default=0)
    quiz_attempts = Column(Integer, default=0)
    quiz_best_score = Column(DECIMAL(5, 2))
    mastery_level = Column(String(20))
    notes = Column(Text)


class JapaneseVocabProgressDB(Base):
    __tablename__ = "japanese_vocab_progress"
    
    vocab_progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    vocab_id = Column(UUID(as_uuid=True), ForeignKey("japanese_vocabulary.vocab_id", ondelete="CASCADE"))
    times_reviewed = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    times_incorrect = Column(Integer, default=0)
    srs_level = Column(Integer, default=1)
    next_review_date = Column(TIMESTAMP)
    last_reviewed_at = Column(TIMESTAMP)
    is_mastered = Column(Boolean, default=False)
    difficulty_rating = Column(Integer)


class JapaneseKanjiProgressDB(Base):
    __tablename__ = "japanese_kanji_progress"
    
    kanji_progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    kanji_id = Column(UUID(as_uuid=True), ForeignKey("japanese_kanji.kanji_id", ondelete="CASCADE"))
    recognition_level = Column(Integer, default=0)
    writing_level = Column(Integer, default=0)
    times_practiced = Column(Integer, default=0)
    last_practiced_at = Column(TIMESTAMP)
    is_mastered = Column(Boolean, default=False)


class JapaneseQuizDB(Base):
    __tablename__ = "japanese_quizzes"
    
    quiz_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("japanese_lessons.lesson_id", ondelete="CASCADE"))
    quiz_title = Column(String(255), nullable=False)
    quiz_type = Column(String(50), nullable=False)
    time_limit_minutes = Column(Integer)
    passing_score = Column(DECIMAL(5, 2), default=70.00)
    questions = Column(JSONB, nullable=False)
    difficulty = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseQuizAttemptDB(Base):
    __tablename__ = "japanese_quiz_attempts"
    
    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("japanese_enrollments.enrollment_id", ondelete="CASCADE"))
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("japanese_quizzes.quiz_id", ondelete="CASCADE"))
    started_at = Column(TIMESTAMP, server_default=func.now())
    submitted_at = Column(TIMESTAMP)
    score = Column(DECIMAL(5, 2))
    answers = Column(JSONB)
    feedback = Column(JSONB)
    time_taken_minutes = Column(Integer)
    passed = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)


class JapaneseMockTestDB(Base):
    __tablename__ = "japanese_mock_tests"
    
    mock_test_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jlpt_level = Column(String(10), nullable=False)
    test_name = Column(String(255), nullable=False)
    sections = Column(JSONB, nullable=False)
    total_questions = Column(Integer, nullable=False)
    time_limit_minutes = Column(Integer, nullable=False)
    passing_score = Column(DECIMAL(5, 2), default=70.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseMockTestAttemptDB(Base):
    __tablename__ = "japanese_mock_test_attempts"
    
    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    mock_test_id = Column(UUID(as_uuid=True), ForeignKey("japanese_mock_tests.mock_test_id", ondelete="CASCADE"))
    started_at = Column(TIMESTAMP, server_default=func.now())
    submitted_at = Column(TIMESTAMP)
    vocabulary_score = Column(DECIMAL(5, 2))
    grammar_score = Column(DECIMAL(5, 2))
    reading_score = Column(DECIMAL(5, 2))
    listening_score = Column(DECIMAL(5, 2))
    total_score = Column(DECIMAL(5, 2))
    passed = Column(Boolean, default=False)
    detailed_results = Column(JSONB)
    weak_areas = Column(JSONB)


class JapaneseSpeakingPracticeDB(Base):
    __tablename__ = "japanese_speaking_practice"
    
    practice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("japanese_lessons.lesson_id"))
    prompt_text = Column(Text, nullable=False)
    audio_recording_url = Column(String(500))
    transcript_romaji = Column(Text)
    transcript_hiragana = Column(Text)
    ai_pronunciation_score = Column(DECIMAL(5, 2))
    ai_feedback = Column(Text)
    ai_pronunciation_details = Column(JSONB)
    recorded_at = Column(TIMESTAMP, server_default=func.now())


class JapaneseWritingPracticeDB(Base):
    __tablename__ = "japanese_writing_practice"
    
    writing_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("japanese_lessons.lesson_id"))
    prompt_text = Column(Text, nullable=False)
    student_writing = Column(Text, nullable=False)
    writing_type = Column(String(50))
    ai_grammar_check = Column(JSONB)
    ai_feedback = Column(Text)
    teacher_feedback = Column(Text)
    score = Column(DECIMAL(5, 2))
    submitted_at = Column(TIMESTAMP, server_default=func.now())
    reviewed_at = Column(TIMESTAMP)


class JapaneseCertificateDB(Base):
    __tablename__ = "japanese_certificates"
    
    certificate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("japanese_courses.course_id", ondelete="CASCADE"))
    jlpt_level = Column(String(10), nullable=False)
    certificate_type = Column(String(100), nullable=False)
    final_score = Column(DECIMAL(5, 2))
    issued_at = Column(TIMESTAMP, server_default=func.now())
    certificate_url = Column(String(500))
    certificate_image_url = Column(String(500))
    verification_code = Column(String(50), unique=True, nullable=False)
    linkedin_share_url = Column(String(500))


class JapaneseStudyStreakDB(Base):
    __tablename__ = "japanese_study_streaks"
    
    streak_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_study_date = Column(Date)
    total_study_days = Column(Integer, default=0)
    total_study_minutes = Column(Integer, default=0)
    streak_broken_count = Column(Integer, default=0)


class JapaneseAchievementDB(Base):
    __tablename__ = "japanese_achievements"
    
    achievement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    achievement_type = Column(String(100), nullable=False)
    achievement_name = Column(String(255), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    earned_at = Column(TIMESTAMP, server_default=func.now())
    xp_awarded = Column(Integer, default=0)
