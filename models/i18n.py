"""
Internationalization (i18n) Models
Request/Response schemas for multilingual API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class LanguageInfo(BaseModel):
    """Language information"""
    language_code: str = Field(..., regex="^(ne|en|ja)$")
    language_name_en: str
    language_name_native: str
    is_active: bool = True
    display_order: int = 0
    
    class Config:
        from_attributes = True


class TranslationCreate(BaseModel):
    """Create a new translation"""
    content_type: str = Field(..., max_length=50)
    content_id: str
    language_code: str = Field(..., regex="^(ne|en|ja)$")
    translated_text: str
    audio_url: Optional[str] = None


class TranslationUpdate(BaseModel):
    """Update existing translation"""
    translated_text: Optional[str] = None
    audio_url: Optional[str] = None


class TranslationResponse(BaseModel):
    """Translation response"""
    translation_id: str
    content_type: str
    content_id: str
    language_code: str
    translated_text: str
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentTranslations(BaseModel):
    """All translations for a piece of content"""
    content_id: str
    content_type: str
    translations: Dict[str, str]  # {language_code: translated_text}


class UserLanguagePreference(BaseModel):
    """User's language preference"""
    preferred_language: str = Field(..., regex="^(ne|en|ja)$")


class MultilingualContent(BaseModel):
    """Content with translation in user's preferred language"""
    content_id: str
    content_type: str
    language: str
    text: str
    audio_url: Optional[str] = None
