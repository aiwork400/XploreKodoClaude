"""
Lesson Management API Endpoints
CRUD operations with role-based access control
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid
from typing import List

from models.lesson import LessonCreate, LessonResponse, LessonUpdate, LessonInDB
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

# In-memory lesson storage (will be replaced with database later)
lessons_db = {}


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson_data: LessonCreate,
    admin_user: dict = Depends(require_admin)
):
    """
    Create a new lesson (admin only)
    
    - Validates level (N5-N1)
    - Requires admin role
    - Returns created lesson
    """
    lesson_id = str(uuid.uuid4())
    
    new_lesson = LessonInDB(
        lesson_id=lesson_id,
        level=lesson_data.level,
        title=lesson_data.title,
        description=lesson_data.description,
        content_json=lesson_data.content_json,
        created_at=datetime.utcnow()
    )
    
    lessons_db[lesson_id] = new_lesson
    
    return LessonResponse(
        lesson_id=new_lesson.lesson_id,
        level=new_lesson.level,
        title=new_lesson.title,
        description=new_lesson.description,
        content_json=new_lesson.content_json,
        created_at=new_lesson.created_at
    )


@router.get("", response_model=List[LessonResponse])
async def list_lessons():
    """
    List all lessons (public access)
    
    - No authentication required
    - Returns all lessons
    """
    return [
        LessonResponse(
            lesson_id=lesson.lesson_id,
            level=lesson.level,
            title=lesson.title,
            description=lesson.description,
            content_json=lesson.content_json,
            created_at=lesson.created_at
        )
        for lesson in lessons_db.values()
    ]


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str):
    """
    Get specific lesson (public access)
    
    - No authentication required
    - Returns 404 if not found
    """
    lesson = lessons_db.get(lesson_id)
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        level=lesson.level,
        title=lesson.title,
        description=lesson.description,
        content_json=lesson.content_json,
        created_at=lesson.created_at
    )


@router.put("/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: str,
    lesson_data: LessonUpdate,
    admin_user: dict = Depends(require_admin)
):
    """
    Update a lesson (admin only)
    
    - Requires admin role
    - Returns 404 if not found
    - Returns updated lesson
    """
    lesson = lessons_db.get(lesson_id)
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Update lesson
    updated_lesson = LessonInDB(
        lesson_id=lesson.lesson_id,
        level=lesson_data.level,
        title=lesson_data.title,
        description=lesson_data.description,
        content_json=lesson_data.content_json,
        created_at=lesson.created_at
    )
    
    lessons_db[lesson_id] = updated_lesson
    
    return LessonResponse(
        lesson_id=updated_lesson.lesson_id,
        level=updated_lesson.level,
        title=updated_lesson.title,
        description=updated_lesson.description,
        content_json=updated_lesson.content_json,
        created_at=updated_lesson.created_at
    )


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    admin_user: dict = Depends(require_admin)
):
    """
    Delete a lesson (admin only)
    
    - Requires admin role
    - Returns 404 if not found
    - Returns success message
    """
    lesson = lessons_db.get(lesson_id)
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    del lessons_db[lesson_id]
    
    return {"message": "Lesson deleted successfully"}
