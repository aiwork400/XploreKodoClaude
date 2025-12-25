"""
Certificate Generation API - Database Version
Generate certificates for completed lessons with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import List

from models.certificate import CertificateResponse
from db_models.certificate import CertificateDB
from db_models.progress import ProgressDB
from config.database import get_db
from config.dependencies import get_current_user

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.post("/generate/{lesson_id}", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def generate_certificate(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate a certificate after completing a lesson - stores in PostgreSQL"""
    
    # Check if user has completed the lesson (100% progress)
    progress = db.query(ProgressDB).filter(
        ProgressDB.user_id == current_user["user_id"],
        ProgressDB.lesson_id == lesson_id
    ).first()
    
    if not progress or progress.completed_percentage < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lesson must be 100% complete to generate certificate"
        )
    
    # Check if certificate already exists
    existing_cert = db.query(CertificateDB).filter(
        CertificateDB.user_id == current_user["user_id"],
        CertificateDB.lesson_id == lesson_id
    ).first()
    
    if existing_cert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate already exists for this lesson"
        )
    
    # Create certificate
    certificate_id = str(uuid.uuid4())
    
    new_certificate = CertificateDB(
        certificate_id=certificate_id,
        user_id=current_user["user_id"],
        lesson_id=lesson_id,
        issued_at=datetime.utcnow()
    )
    
    db.add(new_certificate)
    db.commit()
    db.refresh(new_certificate)
    
    return CertificateResponse(
        certificate_id=new_certificate.certificate_id,
        user_id=new_certificate.user_id,
        lesson_id=new_certificate.lesson_id,
        issued_at=new_certificate.issued_at
    )


@router.get("/my-certificates", response_model=List[CertificateResponse])
async def get_my_certificates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all certificates for current user from PostgreSQL"""
    certificates = db.query(CertificateDB).filter(
        CertificateDB.user_id == current_user["user_id"]
    ).all()
    
    return [
        CertificateResponse(
            certificate_id=cert.certificate_id,
            user_id=cert.user_id,
            lesson_id=cert.lesson_id,
            issued_at=cert.issued_at
        )
        for cert in certificates
    ]
