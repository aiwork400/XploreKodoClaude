"""
Dashboard API Endpoint
User statistics and analytics
"""
from fastapi import APIRouter, Depends

from models.dashboard import DashboardStats
from config.dependencies import get_current_user
from api.progress import progress_db
from api.certificates import certificates_db
from api.quizzes import quiz_attempts_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/my-stats", response_model=DashboardStats)
async def get_my_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """
    Get comprehensive dashboard statistics for current user
    
    - Total lessons enrolled (with any progress)
    - Lessons completed (100% progress)
    - Certificates earned
    - Quizzes taken
    - Average quiz score
    """
    user_id = current_user.get("user_id")
    
    # Count lessons enrolled (any progress recorded)
    user_progress = [p for p in progress_db.values() if p.user_id == user_id]
    total_lessons_enrolled = len(user_progress)
    
    # Count completed lessons (100% progress)
    lessons_completed = len([p for p in user_progress if p.completed_percentage == 100])
    
    # Count certificates earned
    certificates_earned = len([c for c in certificates_db.values() if c.user_id == user_id])
    
    # Get quiz statistics
    user_quiz_attempts = [a for a in quiz_attempts_db.values() if a.user_id == user_id]
    quizzes_taken = len(user_quiz_attempts)
    
    # Calculate average quiz score
    if quizzes_taken > 0:
        total_score = sum(attempt.score for attempt in user_quiz_attempts)
        average_quiz_score = total_score / quizzes_taken
    else:
        average_quiz_score = 0.0
    
    return DashboardStats(
        total_lessons_enrolled=total_lessons_enrolled,
        lessons_completed=lessons_completed,
        certificates_earned=certificates_earned,
        quizzes_taken=quizzes_taken,
        average_quiz_score=average_quiz_score
    )
