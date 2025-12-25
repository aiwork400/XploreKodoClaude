"""
AI Widget Models
Request/Response schemas for chat system
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessageCreate(BaseModel):
    """Create a new chat message"""
    content: str = Field(..., min_length=1, max_length=5000)
    audio_url: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Chat message response"""
    message_id: str
    conversation_id: str
    role: str
    content: str
    audio_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatConversationCreate(BaseModel):
    """Create a new chat conversation"""
    title: Optional[str] = None
    language_code: str = Field(default="en", regex="^(ne|en|ja)$")


class ChatConversationResponse(BaseModel):
    """Chat conversation response"""
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    language_code: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatConversationWithMessages(BaseModel):
    """Conversation with messages"""
    conversation_id: str
    title: Optional[str] = None
    language_code: str
    messages: List[ChatMessageResponse]
    created_at: datetime
    updated_at: datetime


class WidgetSettingsUpdate(BaseModel):
    """Update widget settings"""
    widget_voice_enabled: Optional[bool] = None
    widget_avatar_enabled: Optional[bool] = None
    widget_auto_language: Optional[bool] = None


class WidgetSettingsResponse(BaseModel):
    """Widget settings response"""
    widget_voice_enabled: bool
    widget_avatar_enabled: bool
    widget_auto_language: bool
    preferred_language: str


class AIWidgetSessionCreate(BaseModel):
    """Create AI widget session"""
    session_type: str = Field(..., regex="^(text|voice|avatar)$")


class AIWidgetSessionResponse(BaseModel):
    """AI widget session response"""
    session_id: str
    session_type: str
    message_count: int
    duration_seconds: int
    cost_tokens: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request for AI chat"""
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=5000)
    language: Optional[str] = Field(default=None, regex="^(ne|en|ja)$")
    use_voice: bool = False
    use_avatar: bool = False


class ChatResponse(BaseModel):
    """Response from AI chat"""
    conversation_id: str
    message_id: str
    content: str
    audio_url: Optional[str] = None
    language: str
    tokens_used: int
