"""
Database Model - Lesson
"""
from sqlalchemy import Column, String, DateTime, JSON
from config.database import Base


class LessonDB(Base):
    __tablename__ = "lessons"
    
    lesson_id = Column(String, primary_key=True, index=True)
    level = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    content_json = Column(JSON)
    created_at = Column(DateTime, nullable=False)
