"""
User Models (Pydantic)
Request/Response schemas for API
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    student = "student"
    admin = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.student


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserRecord(BaseModel):
    user_id: str
    email: str
    hashed_password: str
    role: UserRole
    created_at: datetime
