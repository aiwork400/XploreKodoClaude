"""
Enrollment Management API - Database Version
Manage lesson enrollments with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends, Response
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List

from models.enrollment import EnrollmentResponse
from db_models.enrollment import EnrollmentDB
from config.database import get_db
from config.dependencies import get_current_user

router = APIRouter(prefix="/api/enrollments", tags=["Enrollments"])


@router.post("/{lesson_id}", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enroll in a lesson - stores in PostgreSQL"""
    
    # Check if already enrolled
    existing_enrollment = db.query(EnrollmentDB).filter(
        EnrollmentDB.user_id == current_user["user_id"],
        EnrollmentDB.lesson_id == lesson_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this lesson"
        )
    
    # Create enrollment
    enrollment_id = str(uuid.uuid4())
    
    new_enrollment = EnrollmentDB(
        enrollment_id=enrollment_id,
        user_id=current_user["user_id"],
        lesson_id=lesson_id,
        status="active",
        enrolled_at=datetime.utcnow()
    )
    
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    
    return EnrollmentResponse(
        enrollment_id=new_enrollment.enrollment_id,
        user_id=new_enrollment.user_id,
        lesson_id=new_enrollment.lesson_id,
        status=new_enrollment.status,
        enrolled_at=new_enrollment.enrolled_at
    )


@router.get("/my-enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all enrollments for current user from PostgreSQL"""
    enrollments = db.query(EnrollmentDB).filter(
        EnrollmentDB.user_id == current_user["user_id"]
    ).all()
    
    return [
        EnrollmentResponse(
            enrollment_id=e.enrollment_id,
            user_id=e.user_id,
            lesson_id=e.lesson_id,
            status=e.status,
            enrolled_at=e.enrolled_at
        )
        for e in enrollments
    ]


@router.get("/status/{lesson_id}")
async def check_enrollment_status(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if user is enrolled in a lesson from PostgreSQL"""
    enrollment = db.query(EnrollmentDB).filter(
        EnrollmentDB.user_id == current_user["user_id"],
        EnrollmentDB.lesson_id == lesson_id
    ).first()
    
    if enrollment:
        return {
            "enrolled": True,
            "enrollment_id": enrollment.enrollment_id,
            "lesson_id": enrollment.lesson_id,
            "status": enrollment.status,
            "enrolled_at": enrollment.enrolled_at
        }
    else:
        return {"enrolled": False}


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_from_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unenroll from a lesson in PostgreSQL"""
    enrollment = db.query(EnrollmentDB).filter(
        EnrollmentDB.user_id == current_user["user_id"],
        EnrollmentDB.lesson_id == lesson_id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    db.delete(enrollment)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
