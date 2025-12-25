"""
Lesson Model
Pydantic models for lesson data
"""
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime


class LessonBase(BaseModel):
    level: str
    title: str
    description: Optional[str] = None
    content_json: Dict[str, Any] = {}
    
    @validator("level")
    def validate_level(cls, v):
        if v not in ["N5", "N4", "N3", "N2", "N1"]:
            raise ValueError("Level must be N5, N4, N3, N2, or N1")
        return v


class LessonCreate(LessonBase):
    pass


class LessonUpdate(LessonBase):
    pass


class LessonResponse(LessonBase):
    lesson_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class LessonInDB(LessonBase):
    lesson_id: str
    created_at: datetime
