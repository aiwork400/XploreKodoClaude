"""
AI/ML Training API Routes
Endpoints for AI/ML courses, code playground, projects, and certifications
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import uuid

from config.database import get_db
from db_models.aiml_training import (
    AIMLCourseDB,
    AIMLLessonDB,
    AIMLEnrollmentDB,
    AIMLLessonProgressDB,
    AIMLCodeSubmissionDB,
    AIMLProjectDB,
    AIMLCertificateDB,
    AIMLLearningPathDB,
    AIMLPathEnrollmentDB,
    AIMLLeaderboardDB,
    AIMLJobPlacementDB
)
from pydantic import BaseModel, Field, HttpUrl
from decimal import Decimal

router = APIRouter(prefix="/api/aiml", tags=["AI/ML Training"])


# ==================== PYDANTIC SCHEMAS ====================

class AIMLCourseResponse(BaseModel):
    course_id: uuid.UUID
    course_name: str
    level: int
    track: Optional[str]
    duration_weeks: int
    price: Decimal
    description: Optional[str]
    is_active: bool
    
    class Config:
        orm_mode = True


class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID


class EnrollmentResponse(BaseModel):
    enrollment_id: uuid.UUID
    user_id: str
    course_id: uuid.UUID
    enrolled_at: datetime
    progress_percentage: Decimal
    status: str
    
    class Config:
        orm_mode = True


class CodeSubmissionCreate(BaseModel):
    lesson_id: uuid.UUID
    code_content: str
    language: str = "python"


class CodeSubmissionResponse(BaseModel):
    submission_id: uuid.UUID
    auto_grade_score: Optional[Decimal]
    ai_feedback: Optional[str]
    passed: bool
    test_results: Optional[dict]
    
    class Config:
        orm_mode = True


class ProjectCreate(BaseModel):
    course_id: uuid.UUID
    project_title: str
    project_type: str
    description: Optional[str]
    github_url: Optional[HttpUrl]
    demo_url: Optional[HttpUrl]
    technologies_used: Optional[dict]


class ProjectResponse(BaseModel):
    project_id: uuid.UUID
    project_title: str
    project_type: str
    github_url: Optional[str]
    demo_url: Optional[str]
    grade: Optional[Decimal]
    is_portfolio_featured: bool
    
    class Config:
        orm_mode = True


class LearningPathResponse(BaseModel):
    path_id: uuid.UUID
    path_name: str
    description: Optional[str]
    total_duration_weeks: int
    total_price: Decimal
    job_placement_guarantee: bool
    
    class Config:
        orm_mode = True


class LeaderboardEntry(BaseModel):
    user_id: str
    total_xp: int
    ranking: int
    projects_completed: int
    badges_earned: Optional[list]
    
    class Config:
        orm_mode = True


# ==================== COURSE ENDPOINTS ====================

@router.get("/courses", response_model=List[AIMLCourseResponse])
def get_all_courses(
    level: Optional[int] = None,
    track: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all AI/ML courses"""
    query = db.query(AIMLCourseDB).filter(AIMLCourseDB.is_active == True)
    
    if level:
        query = query.filter(AIMLCourseDB.level == level)
    
    if track:
        query = query.filter(AIMLCourseDB.track == track)
    
    courses = query.order_by(AIMLCourseDB.level).all()
    return courses


@router.get("/courses/{course_id}", response_model=AIMLCourseResponse)
def get_course_by_id(course_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get course details by ID"""
    course = db.query(AIMLCourseDB).filter(
        AIMLCourseDB.course_id == course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course


@router.get("/courses/{course_id}/syllabus")
def get_course_syllabus(course_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get detailed course syllabus with all lessons"""
    course = db.query(AIMLCourseDB).filter(
        AIMLCourseDB.course_id == course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lessons = db.query(AIMLLessonDB).filter(
        AIMLLessonDB.course_id == course_id
    ).order_by(
        AIMLLessonDB.week_number,
        AIMLLessonDB.sort_order
    ).all()
    
    # Group by week
    syllabus = {}
    for lesson in lessons:
        week = f"Week {lesson.week_number}"
        if week not in syllabus:
            syllabus[week] = []
        
        syllabus[week].append({
            "lesson_id": str(lesson.lesson_id),
            "lesson_title": lesson.lesson_title,
            "lesson_type": lesson.lesson_type,
            "duration_minutes": lesson.duration_minutes,
            "jupyter_notebook_url": lesson.jupyter_notebook_url,
            "dataset_url": lesson.dataset_url
        })
    
    return {
        "course": AIMLCourseResponse.from_orm(course),
        "syllabus": syllabus,
        "total_lessons": len(lessons)
    }


# ==================== ENROLLMENT ENDPOINTS ====================

@router.post("/enrollments", response_model=EnrollmentResponse)
def enroll_in_course(
    enrollment_data: EnrollmentCreate,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Enroll in an AI/ML course"""
    course = db.query(AIMLCourseDB).filter(
        AIMLCourseDB.course_id == enrollment_data.course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check existing enrollment
    existing = db.query(AIMLEnrollmentDB).filter(
        AIMLEnrollmentDB.user_id == current_user_id,
        AIMLEnrollmentDB.course_id == enrollment_data.course_id,
        AIMLEnrollmentDB.status.in_(["enrolled", "active"])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
    
    enrollment = AIMLEnrollmentDB(
        user_id=current_user_id,
        course_id=enrollment_data.course_id,
        status="enrolled"
    )
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return enrollment


@router.get("/enrollments/my-courses", response_model=List[EnrollmentResponse])
def get_my_enrollments(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's AI/ML course enrollments"""
    enrollments = db.query(AIMLEnrollmentDB).filter(
        AIMLEnrollmentDB.user_id == current_user_id
    ).all()
    
    return enrollments


# ==================== CODE PLAYGROUND ENDPOINTS ====================

@router.post("/code/submit", response_model=CodeSubmissionResponse)
def submit_code(
    submission: CodeSubmissionCreate,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Submit code for auto-grading"""
    # Create submission record
    code_submission = AIMLCodeSubmissionDB(
        user_id=current_user_id,
        lesson_id=submission.lesson_id,
        code_content=submission.code_content,
        language=submission.language
    )
    
    # TODO: Implement actual auto-grading logic
    # For now, return mock results
    code_submission.auto_grade_score = Decimal("85.00")
    code_submission.ai_feedback = "Good implementation! Consider optimizing the loop."
    code_submission.passed = True
    code_submission.test_results = {
        "total_tests": 10,
        "passed": 8,
        "failed": 2
    }
    
    db.add(code_submission)
    db.commit()
    db.refresh(code_submission)
    
    return code_submission


@router.get("/code/history")
def get_code_submission_history(
    current_user_id: str = "user_001",  # TODO: Get from auth
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's code submission history"""
    submissions = db.query(AIMLCodeSubmissionDB).filter(
        AIMLCodeSubmissionDB.user_id == current_user_id
    ).order_by(
        AIMLCodeSubmissionDB.submitted_at.desc()
    ).limit(limit).all()
    
    return submissions


# ==================== PROJECT ENDPOINTS ====================

@router.post("/projects", response_model=ProjectResponse)
def submit_project(
    project_data: ProjectCreate,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Submit an AI/ML project"""
    project = AIMLProjectDB(
        user_id=current_user_id,
        course_id=project_data.course_id,
        project_title=project_data.project_title,
        project_type=project_data.project_type,
        description=project_data.description,
        github_url=str(project_data.github_url) if project_data.github_url else None,
        demo_url=str(project_data.demo_url) if project_data.demo_url else None,
        technologies_used=project_data.technologies_used
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/projects/my-projects", response_model=List[ProjectResponse])
def get_my_projects(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's AI/ML projects"""
    projects = db.query(AIMLProjectDB).filter(
        AIMLProjectDB.user_id == current_user_id
    ).order_by(
        AIMLProjectDB.submitted_at.desc()
    ).all()
    
    return projects


@router.get("/projects/portfolio")
def get_featured_projects(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's portfolio-featured projects"""
    projects = db.query(AIMLProjectDB).filter(
        AIMLProjectDB.user_id == current_user_id,
        AIMLProjectDB.is_portfolio_featured == True
    ).all()
    
    return projects


@router.put("/projects/{project_id}/feature")
def feature_project_in_portfolio(
    project_id: uuid.UUID,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Feature project in portfolio"""
    project = db.query(AIMLProjectDB).filter(
        AIMLProjectDB.project_id == project_id,
        AIMLProjectDB.user_id == current_user_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.is_portfolio_featured = True
    db.commit()
    
    return {"message": "Project featured in portfolio"}


# ==================== LEARNING PATH ENDPOINTS ====================

@router.get("/learning-paths", response_model=List[LearningPathResponse])
def get_learning_paths(db: Session = Depends(get_db)):
    """Get all AI/ML learning paths"""
    paths = db.query(AIMLLearningPathDB).filter(
        AIMLLearningPathDB.is_active == True
    ).all()
    
    return paths


@router.post("/learning-paths/{path_id}/enroll")
def enroll_in_path(
    path_id: uuid.UUID,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Enroll in a learning path"""
    path = db.query(AIMLLearningPathDB).filter(
        AIMLLearningPathDB.path_id == path_id
    ).first()
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    # Check existing enrollment
    existing = db.query(AIMLPathEnrollmentDB).filter(
        AIMLPathEnrollmentDB.user_id == current_user_id,
        AIMLPathEnrollmentDB.path_id == path_id,
        AIMLPathEnrollmentDB.status == "active"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this path")
    
    enrollment = AIMLPathEnrollmentDB(
        user_id=current_user_id,
        path_id=path_id,
        status="active"
    )
    
    db.add(enrollment)
    db.commit()
    
    return {"message": "Enrolled in learning path", "path_name": path.path_name}


# ==================== LEADERBOARD ENDPOINTS ====================

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get AI/ML training leaderboard"""
    entries = db.query(AIMLLeaderboardDB).order_by(
        AIMLLeaderboardDB.total_xp.desc()
    ).limit(limit).all()
    
    # Update rankings
    for idx, entry in enumerate(entries, start=1):
        entry.ranking = idx
    
    db.commit()
    
    return entries


@router.get("/leaderboard/my-rank")
def get_my_rank(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's leaderboard position"""
    entry = db.query(AIMLLeaderboardDB).filter(
        AIMLLeaderboardDB.user_id == current_user_id
    ).first()
    
    if not entry:
        # Create entry if doesn't exist
        entry = AIMLLeaderboardDB(user_id=current_user_id)
        db.add(entry)
        db.commit()
        db.refresh(entry)
    
    return entry


@router.post("/leaderboard/add-xp")
def add_xp(
    xp_amount: int,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Add XP to user's total"""
    entry = db.query(AIMLLeaderboardDB).filter(
        AIMLLeaderboardDB.user_id == current_user_id
    ).first()
    
    if not entry:
        entry = AIMLLeaderboardDB(user_id=current_user_id)
        db.add(entry)
    
    entry.total_xp += xp_amount
    entry.last_updated = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Added {xp_amount} XP", "total_xp": entry.total_xp}


# ==================== CERTIFICATE ENDPOINTS ====================

@router.get("/certificates/my-certs")
def get_my_certificates(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's AI/ML certificates"""
    certs = db.query(AIMLCertificateDB).filter(
        AIMLCertificateDB.user_id == current_user_id
    ).all()
    
    return certs


@router.get("/certificates/{certificate_id}/verify")
def verify_certificate(certificate_id: uuid.UUID, db: Session = Depends(get_db)):
    """Verify AI/ML certificate (public)"""
    cert = db.query(AIMLCertificateDB).filter(
        AIMLCertificateDB.certificate_id == certificate_id
    ).first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {
        "valid": True,
        "certificate_type": cert.certificate_type,
        "issued_at": cert.issued_at,
        "verification_code": cert.verification_code,
        "industry_recognized": cert.is_industry_recognized
    }


# ==================== JOB PLACEMENT ENDPOINTS ====================

@router.post("/placements")
def record_job_placement(
    company_name: str,
    job_title: str,
    salary_jpy: Decimal,
    placement_date: date,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Record successful job placement"""
    placement = AIMLJobPlacementDB(
        user_id=current_user_id,
        company_name=company_name,
        job_title=job_title,
        salary_jpy=salary_jpy,
        placement_date=placement_date,
        placement_fee=salary_jpy * Decimal("0.10")  # 10% fee
    )
    
    db.add(placement)
    db.commit()
    
    return {
        "message": "Job placement recorded",
        "placement_fee": float(placement.placement_fee)
    }


@router.get("/placements/stats")
def get_placement_stats(db: Session = Depends(get_db)):
    """Get job placement statistics"""
    total_placements = db.query(AIMLJobPlacementDB).count()
    avg_salary = db.query(AIMLJobPlacementDB).with_entities(
        func.avg(AIMLJobPlacementDB.salary_jpy)
    ).scalar()
    
    return {
        "total_placements": total_placements,
        "average_salary_jpy": float(avg_salary) if avg_salary else 0,
        "placement_guarantee": "80% for ML Engineer path"
    }


# ==================== HEALTH CHECK ====================

@router.get("/health")
def aiml_training_health():
    """Health check for AI/ML training module"""
    return {
        "status": "healthy",
        "module": "AI/ML Training",
        "version": "1.0.0"
    }
