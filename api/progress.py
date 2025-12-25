"""
Progress Tracking API - Database Version
Track user progress through lessons with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List

from models.progress import ProgressCreate, ProgressUpdate, ProgressResponse
from db_models.progress import ProgressDB
from config.database import get_db
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.post("", response_model=ProgressResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_progress(
    progress_data: ProgressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create or update progress for a lesson - stores in PostgreSQL"""
    
    # Validate percentage
    if not 0 <= progress_data.completed_percentage <= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage must be between 0 and 100"
        )
    
    # Check if progress already exists
    existing_progress = db.query(ProgressDB).filter(
        ProgressDB.user_id == current_user["user_id"],
        ProgressDB.lesson_id == progress_data.lesson_id
    ).first()
    
    if existing_progress:
        # Update existing progress
        existing_progress.completed_percentage = progress_data.completed_percentage
        if progress_data.notes:
            existing_progress.notes = progress_data.notes
        existing_progress.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_progress)
        
        return ProgressResponse(
            progress_id=existing_progress.progress_id,
            user_id=existing_progress.user_id,
            lesson_id=existing_progress.lesson_id,
            completed_percentage=existing_progress.completed_percentage,
            notes=existing_progress.notes,
            last_updated=existing_progress.last_updated
        )
    else:
        # Create new progress
        progress_id = str(uuid.uuid4())
        
        new_progress = ProgressDB(
            progress_id=progress_id,
            user_id=current_user["user_id"],
            lesson_id=progress_data.lesson_id,
            completed_percentage=progress_data.completed_percentage,
            notes=progress_data.notes,
            last_updated=datetime.utcnow()
        )
        
        db.add(new_progress)
        db.commit()
        db.refresh(new_progress)
        
        return ProgressResponse(
            progress_id=new_progress.progress_id,
            user_id=new_progress.user_id,
            lesson_id=new_progress.lesson_id,
            completed_percentage=new_progress.completed_percentage,
            notes=new_progress.notes,
            last_updated=new_progress.last_updated
        )


@router.get("/my-progress", response_model=List[ProgressResponse])
async def get_my_progress(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all progress for current user from PostgreSQL"""
    progress_records = db.query(ProgressDB).filter(
        ProgressDB.user_id == current_user["user_id"]
    ).all()
    
    return [
        ProgressResponse(
            progress_id=p.progress_id,
            user_id=p.user_id,
            lesson_id=p.lesson_id,
            completed_percentage=p.completed_percentage,
            notes=p.notes,
            last_updated=p.last_updated
        )
        for p in progress_records
    ]


@router.get("/lesson/{lesson_id}/stats")
async def get_lesson_progress_stats(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get progress statistics for a lesson (admin only) from PostgreSQL"""
    progress_records = db.query(ProgressDB).filter(
        ProgressDB.lesson_id == lesson_id
    ).all()
    
    if not progress_records:
        return {
            "lesson_id": lesson_id,
            "total_students": 0,
            "average_completion": 0,
            "completed_students": 0
        }
    
    total_students = len(progress_records)
    total_percentage = sum(p.completed_percentage for p in progress_records)
    average_completion = total_percentage / total_students if total_students > 0 else 0
    completed_students = sum(1 for p in progress_records if p.completed_percentage == 100)
    
    return {
        "lesson_id": lesson_id,
        "total_students": total_students,
        "average_completion": round(average_completion, 2),
        "completed_students": completed_students
    }
