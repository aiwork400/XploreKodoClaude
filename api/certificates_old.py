"""
Certificate API Endpoints
Certificate generation for completed lessons
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid
from typing import List

from models.certificate import CertificateResponse, CertificateRecord
from config.dependencies import get_current_user
from api.progress import progress_db

router = APIRouter(prefix="/api/certificates", tags=["certificates"])

# In-memory certificate storage (will be replaced with database later)
certificates_db = {}


@router.post("/generate/{lesson_id}", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def generate_certificate(
    lesson_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate certificate for completed lesson
    
    - User must have 100% completion on the lesson
    - Cannot generate duplicate certificates
    - Returns certificate details
    """
    user_id = current_user.get("user_id")
    
    # Check if already has certificate for this lesson
    existing_cert = None
    for cert in certificates_db.values():
        if cert.user_id == user_id and cert.lesson_id == lesson_id:
            existing_cert = cert
            break
    
    if existing_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate already issued for this lesson"
        )
    
    # Check if lesson is 100% complete
    progress_key = f"{user_id}:{lesson_id}"
    progress = progress_db.get(progress_key)
    
    if not progress or progress.completed_percentage < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson must be 100% complete to generate certificate"
        )
    
    # Generate certificate
    certificate_id = str(uuid.uuid4())
    
    new_certificate = CertificateRecord(
        certificate_id=certificate_id,
        user_id=user_id,
        lesson_id=lesson_id,
        issued_at=datetime.utcnow()
    )
    
    certificates_db[certificate_id] = new_certificate
    
    return CertificateResponse(
        certificate_id=new_certificate.certificate_id,
        user_id=new_certificate.user_id,
        lesson_id=new_certificate.lesson_id,
        issued_at=new_certificate.issued_at
    )


@router.get("/my-certificates", response_model=List[CertificateResponse])
async def get_my_certificates(current_user: dict = Depends(get_current_user)):
    """
    Get current user's certificates
    
    - Returns list of all certificates for the authenticated user
    - Shows completion achievements
    """
    user_id = current_user.get("user_id")
    
    user_certificates = [
        CertificateResponse(
            certificate_id=cert.certificate_id,
            user_id=cert.user_id,
            lesson_id=cert.lesson_id,
            issued_at=cert.issued_at
        )
        for cert in certificates_db.values()
        if cert.user_id == user_id
    ]
    
    return user_certificates
