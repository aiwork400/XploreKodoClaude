"""
Database Models - User
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, String, DateTime, Enum, Boolean
from config.database import Base
import enum

class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"

class UserDB(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.student)
    preferred_language = Column(String(5), default='en')
    widget_voice_enabled = Column(Boolean, default=False)
    widget_avatar_enabled = Column(Boolean, default=False)
    widget_auto_language = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)