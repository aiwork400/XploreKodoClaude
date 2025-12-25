"""
Lesson Management API - Database Version
CRUD operations for Japanese lessons with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List

from models.lesson import LessonCreate, LessonUpdate, LessonResponse
from db_models.lesson import LessonDB
from config.database import get_db
from config.dependencies import require_admin

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson: LessonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new lesson (admin only) - stores in PostgreSQL"""
    lesson_id = str(uuid.uuid4())
    
    new_lesson = LessonDB(
        lesson_id=lesson_id,
        level=lesson.level,
        title=lesson.title,
        description=lesson.description,
        content_json=lesson.content_json,
        created_at=datetime.utcnow()
    )
    
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    
    return LessonResponse(
        lesson_id=new_lesson.lesson_id,
        level=new_lesson.level,
        title=new_lesson.title,
        description=new_lesson.description,
        content_json=new_lesson.content_json,
        created_at=new_lesson.created_at
    )


@router.get("", response_model=List[LessonResponse])
async def get_all_lessons(db: Session = Depends(get_db)):
    """Get all lessons from PostgreSQL"""
    lessons = db.query(LessonDB).all()
    
    return [
        LessonResponse(
            lesson_id=lesson.lesson_id,
            level=lesson.level,
            title=lesson.title,
            description=lesson.description,
            content_json=lesson.content_json,
            created_at=lesson.created_at
        )
        for lesson in lessons
    ]


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """Get specific lesson by ID from PostgreSQL"""
    lesson = db.query(LessonDB).filter(LessonDB.lesson_id == lesson_id).first()
    
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
    lesson_update: LessonUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a lesson (admin only) in PostgreSQL"""
    lesson = db.query(LessonDB).filter(LessonDB.lesson_id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Update fields if provided
    if lesson_update.level is not None:
        lesson.level = lesson_update.level
    if lesson_update.title is not None:
        lesson.title = lesson_update.title
    if lesson_update.description is not None:
        lesson.description = lesson_update.description
    if lesson_update.content_json is not None:
        lesson.content_json = lesson_update.content_json
    
    db.commit()
    db.refresh(lesson)
    
    return LessonResponse(
        lesson_id=lesson.lesson_id,
        level=lesson.level,
        title=lesson.title,
        description=lesson.description,
        content_json=lesson.content_json,
        created_at=lesson.created_at
    )


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a lesson (admin only) from PostgreSQL"""
    lesson = db.query(LessonDB).filter(LessonDB.lesson_id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    db.delete(lesson)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
