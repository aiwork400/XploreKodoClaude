"""
Certificate Model
Pydantic models for certificate data
"""
from pydantic import BaseModel
from datetime import datetime


class CertificateResponse(BaseModel):
    certificate_id: str
    user_id: str
    lesson_id: str
    issued_at: datetime
    
    class Config:
        from_attributes = True


class CertificateRecord(BaseModel):
    certificate_id: str
    user_id: str
    lesson_id: str
    issued_at: datetime
