"""
Quiz Models (Pydantic)
Request/Response schemas for API
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any


class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: str


class QuizCreate(BaseModel):
    lesson_id: str
    title: str
    questions: List[Dict[str, Any]]


class QuizResponse(BaseModel):
    quiz_id: str
    lesson_id: str
    title: str
    questions: List[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuizSubmission(BaseModel):
    answers: Dict[str, str]


class QuizResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: float
    total_questions: int
    correct_answers: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True


class QuizAttemptResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    user_id: str
    score: float
    total_questions: int
    correct_answers: int
    submitted_at: datetime
    
    class Config:
        from_attributes = True


class QuizRecord(BaseModel):
    quiz_id: str
    lesson_id: str
    title: str
    questions: List[Dict[str, Any]]
    created_at: datetime


class QuizAttemptRecord(BaseModel):
    attempt_id: str
    quiz_id: str
    user_id: str
    answers: Dict[str, str]
    score: float
    total_questions: int
    correct_answers: int
    submitted_at: datetime
