"""
Progress Tracking API Endpoints
Track user progress through lessons
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid
from typing import List

from models.progress import ProgressCreate, ProgressResponse, ProgressInDB, LessonProgressStats
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/progress", tags=["progress"])

# In-memory progress storage (will be replaced with database later)
# Key: (user_id, lesson_id) -> Progress
progress_db = {}


@router.post("", response_model=ProgressResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_progress(
    progress_data: ProgressCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create or update user's progress for a lesson
    
    - Authenticated users can track their own progress
    - If progress exists for user+lesson, it updates
    - If not, creates new progress entry
    """
    user_id = current_user.get("user_id")
    lesson_id = progress_data.lesson_id
    
    # Create unique key for user+lesson combination
    progress_key = f"{user_id}:{lesson_id}"
    
    # Check if progress already exists
    if progress_key in progress_db:
        # Update existing progress
        existing_progress = progress_db[progress_key]
        updated_progress = ProgressInDB(
            progress_id=existing_progress.progress_id,
            user_id=user_id,
            lesson_id=lesson_id,
            completed_percentage=progress_data.completed_percentage,
            notes=progress_data.notes,
            last_updated=datetime.utcnow()
        )
        progress_db[progress_key] = updated_progress
        
        return ProgressResponse(
            progress_id=updated_progress.progress_id,
            user_id=updated_progress.user_id,
            lesson_id=updated_progress.lesson_id,
            completed_percentage=updated_progress.completed_percentage,
            notes=updated_progress.notes,
            last_updated=updated_progress.last_updated
        )
    else:
        # Create new progress
        progress_id = str(uuid.uuid4())
        
        new_progress = ProgressInDB(
            progress_id=progress_id,
            user_id=user_id,
            lesson_id=lesson_id,
            completed_percentage=progress_data.completed_percentage,
            notes=progress_data.notes,
            last_updated=datetime.utcnow()
        )
        
        progress_db[progress_key] = new_progress
        
        return ProgressResponse(
            progress_id=new_progress.progress_id,
            user_id=new_progress.user_id,
            lesson_id=new_progress.lesson_id,
            completed_percentage=new_progress.completed_percentage,
            notes=new_progress.notes,
            last_updated=new_progress.last_updated
        )


@router.get("/my-progress", response_model=List[ProgressResponse])
async def get_my_progress(current_user: dict = Depends(get_current_user)):
    """
    Get current user's progress across all lessons
    
    - Returns list of all progress entries for the authenticated user
    - Only returns user's own progress
    """
    user_id = current_user.get("user_id")
    
    # Filter progress by user_id
    user_progress = [
        ProgressResponse(
            progress_id=progress.progress_id,
            user_id=progress.user_id,
            lesson_id=progress.lesson_id,
            completed_percentage=progress.completed_percentage,
            notes=progress.notes,
            last_updated=progress.last_updated
        )
        for progress in progress_db.values()
        if progress.user_id == user_id
    ]
    
    return user_progress


@router.get("/lesson/{lesson_id}", response_model=LessonProgressStats)
async def get_lesson_progress_stats(
    lesson_id: str,
    admin_user: dict = Depends(require_admin)
):
    """
    Get progress statistics for a specific lesson (admin only)
    
    - Total number of students tracking this lesson
    - Average completion percentage
    - Number of students who completed (100%)
    """
    # Filter progress by lesson_id
    lesson_progress = [
        progress
        for progress in progress_db.values()
        if progress.lesson_id == lesson_id
    ]
    
    total_students = len(lesson_progress)
    
    if total_students == 0:
        return LessonProgressStats(
            lesson_id=lesson_id,
            total_students=0,
            average_completion=0.0,
            students_completed=0
        )
    
    # Calculate stats
    total_percentage = sum(p.completed_percentage for p in lesson_progress)
    average_completion = total_percentage / total_students
    students_completed = sum(1 for p in lesson_progress if p.completed_percentage == 100)
    
    return LessonProgressStats(
        lesson_id=lesson_id,
        total_students=total_students,
        average_completion=round(average_completion, 2),
        students_completed=students_completed
    )
