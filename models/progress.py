"""
Progress Models (Pydantic)
Request/Response schemas for API
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProgressCreate(BaseModel):
    lesson_id: str
    completed_percentage: int
    notes: Optional[str] = None


class ProgressUpdate(BaseModel):
    completed_percentage: Optional[int] = None
    notes: Optional[str] = None


class ProgressResponse(BaseModel):
    progress_id: str
    user_id: str
    lesson_id: str
    completed_percentage: int
    notes: Optional[str] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True


class ProgressRecord(BaseModel):
    progress_id: str
    user_id: str
    lesson_id: str
    completed_percentage: int
    notes: Optional[str] = None
    last_updated: datetime
