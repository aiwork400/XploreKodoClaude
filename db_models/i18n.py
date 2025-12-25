"""
Multilingual Database Models
SQLAlchemy models for i18n support
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, TIMESTAMP, ForeignKey, CheckConstraint
from config.uuid_type import UUID
from sqlalchemy.sql import func
import uuid

from config.database import Base


class ContentTranslationDB(Base):
    """Content translations for multilingual support"""
    __tablename__ = "content_translations"
    
    translation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_type = Column(String(50), nullable=False)  # 'lesson', 'quiz', etc.
    content_id = Column(UUID(as_uuid=True), nullable=False)
    language_code = Column(String(5), nullable=False)
    translated_text = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), ForeignKey('users.user_id'), nullable=True)
    
    __table_args__ = (
        CheckConstraint("language_code IN ('ne', 'en', 'ja')", name='check_language_code'),
    )


class LanguageDB(Base):
    """Available languages in the system"""
    __tablename__ = "languages"
    
    language_code = Column(String(5), primary_key=True)
    language_name_en = Column(String(100), nullable=False)
    language_name_native = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
