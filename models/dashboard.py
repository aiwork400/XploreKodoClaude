"""
Dashboard Model
Pydantic models for user dashboard statistics
"""
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_lessons_enrolled: int
    lessons_completed: int
    certificates_earned: int
    quizzes_taken: int
    average_quiz_score: float
