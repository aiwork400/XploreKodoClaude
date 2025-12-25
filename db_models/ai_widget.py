"""
AI Widget Database Models
SQLAlchemy models for chat system
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, CheckConstraint
from config.uuid_type import UUID
from sqlalchemy.sql import func
import uuid

from config.database import Base


class ChatConversationDB(Base):
    """Chat conversation sessions"""
    __tablename__ = "chat_conversations"
    
    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    title = Column(String(255), nullable=True)
    language_code = Column(String(5), default='en')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("language_code IN ('ne', 'en', 'ja')", name='check_conv_language'),
    )


class ChatMessageDB(Base):
    """Individual chat messages"""
    __tablename__ = "chat_messages"
    
    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.conversation_id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_message_role'),
    )


class AIWidgetSessionDB(Base):
    """AI widget usage sessions for billing tracking"""
    __tablename__ = "ai_widget_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey('users.user_id'), nullable=False)
    session_type = Column(String(20), nullable=False)
    message_count = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    cost_tokens = Column(Integer, default=0)
    started_at = Column(TIMESTAMP, server_default=func.now())
    ended_at = Column(TIMESTAMP, nullable=True)
    
    __table_args__ = (
        CheckConstraint("session_type IN ('text', 'voice', 'avatar')", name='check_session_type'),
    )
