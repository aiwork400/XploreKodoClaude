"""
Dashboard Analytics API - Database Version
User statistics and analytics with PostgreSQL
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.dashboard import DashboardStats
from db_models.progress import ProgressDB
from db_models.certificate import CertificateDB
from db_models.quiz import QuizAttemptDB
from config.database import get_db
from config.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/my-stats", response_model=DashboardStats)
async def get_my_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics for current user from PostgreSQL"""
    
    user_id = current_user["user_id"]
    
    # Get progress data
    all_progress = db.query(ProgressDB).filter(ProgressDB.user_id == user_id).all()
    total_lessons_enrolled = len(all_progress)
    lessons_completed = sum(1 for p in all_progress if p.completed_percentage == 100)
    
    # Get certificates
    certificates = db.query(CertificateDB).filter(CertificateDB.user_id == user_id).all()
    certificates_earned = len(certificates)
    
    # Get quiz attempts
    quiz_attempts = db.query(QuizAttemptDB).filter(QuizAttemptDB.user_id == user_id).all()
    quizzes_taken = len(quiz_attempts)
    
    # Calculate average quiz score
    if quizzes_taken > 0:
        total_score = sum(attempt.score for attempt in quiz_attempts)
        average_quiz_score = round(total_score / quizzes_taken, 2)
    else:
        average_quiz_score = 0.0
    
    return DashboardStats(
        total_lessons_enrolled=total_lessons_enrolled,
        lessons_completed=lessons_completed,
        certificates_earned=certificates_earned,
        quizzes_taken=quizzes_taken,
        average_quiz_score=average_quiz_score
    )
