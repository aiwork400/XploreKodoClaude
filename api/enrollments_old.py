"""
Enrollment API Endpoints
Lesson enrollment management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid
from typing import List

from models.enrollment import EnrollmentResponse, EnrollmentRecord, EnrollmentStatusResponse
from config.dependencies import get_current_user

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])

# In-memory enrollment storage (will be replaced with database later)
# Key: (user_id, lesson_id) -> Enrollment
enrollments_db = {}


@router.post("/{lesson_id}", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_lesson(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Enroll user in a lesson
    
    - Authenticated users can enroll in lessons
    - Cannot enroll twice in the same lesson
    """
    user_id = current_user.get("user_id")
    
    # Check if already enrolled
    enrollment_key = f"{user_id}:{lesson_id}"
    if enrollment_key in enrollments_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this lesson"
        )
    
    # Create enrollment
    enrollment_id = str(uuid.uuid4())
    
    new_enrollment = EnrollmentRecord(
        enrollment_id=enrollment_id,
        user_id=user_id,
        lesson_id=lesson_id,
        status="active",
        enrolled_at=datetime.utcnow()
    )
    
    enrollments_db[enrollment_key] = new_enrollment
    
    return EnrollmentResponse(
        enrollment_id=new_enrollment.enrollment_id,
        user_id=new_enrollment.user_id,
        lesson_id=new_enrollment.lesson_id,
        status=new_enrollment.status,
        enrolled_at=new_enrollment.enrolled_at
    )


@router.get("/my-enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(current_user: dict = Depends(get_current_user)):
    """
    Get current user's enrolled lessons
    
    - Returns list of all enrollments for the authenticated user
    - Only returns user's own enrollments
    """
    user_id = current_user.get("user_id")
    
    # Filter enrollments by user_id
    user_enrollments = [
        EnrollmentResponse(
            enrollment_id=enrollment.enrollment_id,
            user_id=enrollment.user_id,
            lesson_id=enrollment.lesson_id,
            status=enrollment.status,
            enrolled_at=enrollment.enrolled_at
        )
        for enrollment in enrollments_db.values()
        if enrollment.user_id == user_id
    ]
    
    return user_enrollments


@router.get("/status/{lesson_id}", response_model=EnrollmentStatusResponse)
async def check_enrollment_status(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Check if user is enrolled in a specific lesson
    
    - Returns enrollment status for the authenticated user
    """
    user_id = current_user.get("user_id")
    enrollment_key = f"{user_id}:{lesson_id}"
    
    enrollment = enrollments_db.get(enrollment_key)
    
    if enrollment:
        return EnrollmentStatusResponse(
            enrolled=True,
            lesson_id=lesson_id,
            enrollment_id=enrollment.enrollment_id
        )
    else:
        return EnrollmentStatusResponse(
            enrolled=False,
            lesson_id=lesson_id
        )


@router.delete("/{lesson_id}")
async def unenroll_from_lesson(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Unenroll user from a lesson
    
    - User can unenroll from their enrolled lessons
    - Returns 404 if not enrolled
    """
    user_id = current_user.get("user_id")
    enrollment_key = f"{user_id}:{lesson_id}"
    
    enrollment = enrollments_db.get(enrollment_key)
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this lesson"
        )
    
    del enrollments_db[enrollment_key]
    
    return {"message": "Successfully unenrolled from lesson"}
