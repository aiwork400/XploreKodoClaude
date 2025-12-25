"""
AI/ML Training Database Models
Level 1-5 courses, projects, and certifications
"""
from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, Text, TIMESTAMP, ForeignKey, Date
from config.uuid_type import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from config.database import Base


class AIMLCourseDB(Base):
    __tablename__ = "aiml_courses"
    
    course_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)
    track = Column(String(50))
    duration_weeks = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text)
    prerequisites = Column(JSONB)
    syllabus_url = Column(String(500))
    learning_objectives = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AIMLLessonDB(Base):
    __tablename__ = "aiml_lessons"
    
    lesson_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("aiml_courses.course_id", ondelete="CASCADE"))
    week_number = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    lesson_title = Column(String(255), nullable=False)
    lesson_type = Column(String(50), nullable=False)
    content_url = Column(String(500))
    jupyter_notebook_url = Column(String(500))
    dataset_url = Column(String(500))
    duration_minutes = Column(Integer)
    difficulty_level = Column(String(20))
    topics = Column(JSONB)
    sort_order = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())


class AIMLEnrollmentDB(Base):
    __tablename__ = "aiml_enrollments"
    
    enrollment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("aiml_courses.course_id", ondelete="CASCADE"))
    enrolled_at = Column(TIMESTAMP, server_default=func.now())
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    progress_percentage = Column(DECIMAL(5, 2), default=0.00)
    status = Column(String(20), default="enrolled")
    final_grade = Column(DECIMAL(5, 2))
    certificate_issued = Column(Boolean, default=False)


class AIMLLessonProgressDB(Base):
    __tablename__ = "aiml_lesson_progress"
    
    progress_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("aiml_enrollments.enrollment_id", ondelete="CASCADE"))
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("aiml_lessons.lesson_id", ondelete="CASCADE"))
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    time_spent_minutes = Column(Integer, default=0)
    status = Column(String(20), default="not_started")
    notes = Column(Text)


class AIMLCodeSubmissionDB(Base):
    __tablename__ = "aiml_code_submissions"
    
    submission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("aiml_lessons.lesson_id", ondelete="CASCADE"))
    code_content = Column(Text, nullable=False)
    language = Column(String(20), default="python")
    submitted_at = Column(TIMESTAMP, server_default=func.now())
    auto_grade_score = Column(DECIMAL(5, 2))
    ai_feedback = Column(Text)
    test_results = Column(JSONB)
    passed = Column(Boolean, default=False)


class AIMLProjectDB(Base):
    __tablename__ = "aiml_projects"
    
    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("aiml_courses.course_id", ondelete="CASCADE"))
    project_title = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False)
    description = Column(Text)
    github_url = Column(String(500))
    demo_url = Column(String(500))
    technologies_used = Column(JSONB)
    submitted_at = Column(TIMESTAMP, server_default=func.now())
    grade = Column(DECIMAL(5, 2))
    feedback = Column(Text)
    is_portfolio_featured = Column(Boolean, default=False)


class AIMLCertificateDB(Base):
    __tablename__ = "aiml_certificates"
    
    certificate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("aiml_courses.course_id", ondelete="CASCADE"))
    certificate_type = Column(String(100), nullable=False)
    final_score = Column(DECIMAL(5, 2))
    issued_at = Column(TIMESTAMP, server_default=func.now())
    certificate_url = Column(String(500))
    verification_code = Column(String(50), unique=True, nullable=False)
    linkedin_share_url = Column(String(500))
    is_industry_recognized = Column(Boolean, default=False)


class AIMLLearningPathDB(Base):
    __tablename__ = "aiml_learning_paths"
    
    path_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_name = Column(String(255), nullable=False)
    description = Column(Text)
    courses = Column(JSONB, nullable=False)
    total_duration_weeks = Column(Integer, nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    job_placement_guarantee = Column(Boolean, default=False)
    guarantee_percentage = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class AIMLPathEnrollmentDB(Base):
    __tablename__ = "aiml_path_enrollments"
    
    path_enrollment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    path_id = Column(UUID(as_uuid=True), ForeignKey("aiml_learning_paths.path_id", ondelete="CASCADE"))
    enrolled_at = Column(TIMESTAMP, server_default=func.now())
    completed_courses = Column(JSONB, default='[]')
    current_course_id = Column(UUID(as_uuid=True), ForeignKey("aiml_courses.course_id"))
    progress_percentage = Column(DECIMAL(5, 2), default=0.00)
    status = Column(String(20), default="active")


class AIMLLeaderboardDB(Base):
    __tablename__ = "aiml_leaderboard"
    
    leaderboard_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    total_xp = Column(Integer, default=0)
    badges_earned = Column(JSONB, default='[]')
    projects_completed = Column(Integer, default=0)
    ranking = Column(Integer)
    last_updated = Column(TIMESTAMP, server_default=func.now())


class AIMLJobPlacementDB(Base):
    __tablename__ = "aiml_job_placements"
    
    placement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    salary_jpy = Column(DECIMAL(12, 2))
    placement_date = Column(Date, nullable=False)
    placement_fee = Column(DECIMAL(10, 2))
    visa_status = Column(String(50))
    is_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
