"""
Database Model - Enrollment
"""
from sqlalchemy import Column, String, DateTime
from config.database import Base


class EnrollmentDB(Base):
    __tablename__ = "enrollments"
    
    enrollment_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    lesson_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    enrolled_at = Column(DateTime, nullable=False)
