"""
Enrollment Models (Pydantic)
Request/Response schemas for API
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EnrollmentCreate(BaseModel):
    lesson_id: str


class EnrollmentResponse(BaseModel):
    enrollment_id: str
    user_id: str
    lesson_id: str
    status: str
    enrolled_at: datetime
    
    class Config:
        from_attributes = True


class EnrollmentRecord(BaseModel):
    enrollment_id: str
    user_id: str
    lesson_id: str
    status: str
    enrolled_at: datetime
