"""
Database Model - Progress
"""
from sqlalchemy import Column, String, DateTime, Integer
from config.database import Base


class ProgressDB(Base):
    __tablename__ = "progress"
    
    progress_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    lesson_id = Column(String, nullable=False, index=True)
    completed_percentage = Column(Integer, nullable=False)
    notes = Column(String)
    last_updated = Column(DateTime, nullable=False)
