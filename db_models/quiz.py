"""
Database Model - Quiz
"""
from sqlalchemy import Column, String, DateTime, JSON, Integer
from config.database import Base


class QuizDB(Base):
    __tablename__ = "quizzes"
    
    quiz_id = Column(String, primary_key=True)
    lesson_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    questions = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)


class QuizAttemptDB(Base):
    __tablename__ = "quiz_attempts"
    
    attempt_id = Column(String, primary_key=True)
    quiz_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    answers = Column(JSON, nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
