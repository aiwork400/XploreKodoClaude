"""
Japanese Language Training API Routes
Endpoints for N5-N1 JLPT courses, lessons, vocabulary, kanji, and progress tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import uuid

from config.database import get_db
from db_models.japanese_training import (
    JapaneseCourseDB,
    JapaneseLessonDB,
    JapaneseVocabularyDB,
    JapaneseKanjiDB,
    JapaneseGrammarDB,
    JapaneseEnrollmentDB,
    JapaneseLessonProgressDB,
    JapaneseVocabProgressDB,
    JapaneseKanjiProgressDB,
    JapaneseQuizDB,
    JapaneseQuizAttemptDB,
    JapaneseMockTestDB,
    JapaneseMockTestAttemptDB,
    JapaneseSpeakingPracticeDB,
    JapaneseWritingPracticeDB,
    JapaneseCertificateDB,
    JapaneseStudyStreakDB,
    JapaneseAchievementDB
)
from pydantic import BaseModel, Field
from decimal import Decimal

router = APIRouter(prefix="/api/japanese", tags=["Japanese Training"])


# ==================== PYDANTIC SCHEMAS ====================

class JapaneseCourseResponse(BaseModel):
    course_id: uuid.UUID
    level: str
    course_name: str
    jlpt_level_num: int
    duration_weeks: int
    price_self_paced: Decimal
    price_interactive: Optional[Decimal]
    price_premium: Optional[Decimal]
    price_vr: Optional[Decimal]
    description: Optional[str]
    vocabulary_count: Optional[int]
    kanji_count: Optional[int]
    grammar_patterns: Optional[int]
    is_active: bool
    
    class Config:
        orm_mode = True


class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID
    delivery_mode: str = Field(..., pattern="^(self_paced|interactive|premium|vr)$")


class EnrollmentResponse(BaseModel):
    enrollment_id: uuid.UUID
    user_id: str
    course_id: uuid.UUID
    delivery_mode: str
    enrolled_at: datetime
    progress_percentage: Decimal
    status: str
    
    class Config:
        orm_mode = True


class VocabularyResponse(BaseModel):
    vocab_id: uuid.UUID
    word_hiragana: str
    word_kanji: Optional[str]
    word_romaji: Optional[str]
    english_meaning: str
    part_of_speech: Optional[str]
    jlpt_level: Optional[str]
    audio_url: Optional[str]
    
    class Config:
        orm_mode = True


class KanjiResponse(BaseModel):
    kanji_id: uuid.UUID
    character: str
    kunyomi: Optional[str]
    onyomi: Optional[str]
    english_meaning: str
    stroke_count: int
    jlpt_level: Optional[str]
    
    class Config:
        orm_mode = True


class QuizAttemptCreate(BaseModel):
    quiz_id: uuid.UUID
    answers: dict


class QuizAttemptResponse(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    score: Optional[Decimal]
    passed: bool
    feedback: Optional[dict]
    
    class Config:
        orm_mode = True


class MockTestAttemptCreate(BaseModel):
    mock_test_id: uuid.UUID


class ProgressResponse(BaseModel):
    progress_percentage: Decimal
    current_week: int
    total_study_minutes: int
    vocabulary_mastered: int
    kanji_mastered: int
    current_streak_days: int
    
    class Config:
        orm_mode = True


# ==================== COURSE ENDPOINTS ====================

@router.get("/courses", response_model=List[JapaneseCourseResponse])
def get_all_courses(
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all Japanese language courses (N5-N1)"""
    query = db.query(JapaneseCourseDB).filter(JapaneseCourseDB.is_active == True)
    
    if level:
        query = query.filter(JapaneseCourseDB.level == level.upper())
    
    courses = query.order_by(JapaneseCourseDB.jlpt_level_num.desc()).all()
    return courses


@router.get("/courses/{course_id}", response_model=JapaneseCourseResponse)
def get_course_by_id(course_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get course details by ID"""
    course = db.query(JapaneseCourseDB).filter(
        JapaneseCourseDB.course_id == course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course


@router.get("/courses/{course_id}/syllabus")
def get_course_syllabus(course_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get detailed course syllabus with all lessons"""
    course = db.query(JapaneseCourseDB).filter(
        JapaneseCourseDB.course_id == course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    lessons = db.query(JapaneseLessonDB).filter(
        JapaneseLessonDB.course_id == course_id
    ).order_by(
        JapaneseLessonDB.week_number,
        JapaneseLessonDB.sort_order
    ).all()
    
    # Group lessons by week
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
            "difficulty": lesson.difficulty_level
        })
    
    return {
        "course": JapaneseCourseResponse.from_orm(course),
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
    """Enroll in a Japanese course"""
    # Check if course exists
    course = db.query(JapaneseCourseDB).filter(
        JapaneseCourseDB.course_id == enrollment_data.course_id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled
    existing = db.query(JapaneseEnrollmentDB).filter(
        JapaneseEnrollmentDB.user_id == current_user_id,
        JapaneseEnrollmentDB.course_id == enrollment_data.course_id,
        JapaneseEnrollmentDB.status.in_(["enrolled", "active"])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")
    
    # Create enrollment
    enrollment = JapaneseEnrollmentDB(
        user_id=current_user_id,
        course_id=enrollment_data.course_id,
        delivery_mode=enrollment_data.delivery_mode,
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
    """Get all courses user is enrolled in"""
    enrollments = db.query(JapaneseEnrollmentDB).filter(
        JapaneseEnrollmentDB.user_id == current_user_id
    ).all()
    
    return enrollments


@router.put("/enrollments/{enrollment_id}/progress")
def update_enrollment_progress(
    enrollment_id: uuid.UUID,
    progress: Decimal,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Update enrollment progress percentage"""
    enrollment = db.query(JapaneseEnrollmentDB).filter(
        JapaneseEnrollmentDB.enrollment_id == enrollment_id,
        JapaneseEnrollmentDB.user_id == current_user_id
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    enrollment.progress_percentage = progress
    enrollment.status = "active"
    
    if progress >= 100:
        enrollment.status = "completed"
        enrollment.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Progress updated", "progress": float(progress)}


# ==================== VOCABULARY ENDPOINTS ====================

@router.get("/vocabulary/level/{level}", response_model=List[VocabularyResponse])
def get_vocabulary_by_level(
    level: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get vocabulary words by JLPT level"""
    vocab = db.query(JapaneseVocabularyDB).filter(
        JapaneseVocabularyDB.jlpt_level == level.upper()
    ).order_by(JapaneseVocabularyDB.frequency_rank).limit(limit).all()
    
    return vocab


@router.get("/vocabulary/{vocab_id}", response_model=VocabularyResponse)
def get_vocabulary_details(vocab_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get detailed vocabulary word information"""
    vocab = db.query(JapaneseVocabularyDB).filter(
        JapaneseVocabularyDB.vocab_id == vocab_id
    ).first()
    
    if not vocab:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    
    return vocab


@router.get("/vocabulary/search")
def search_vocabulary(
    query: str,
    db: Session = Depends(get_db)
):
    """Search vocabulary by hiragana, romaji, or English meaning"""
    results = db.query(JapaneseVocabularyDB).filter(
        (JapaneseVocabularyDB.word_hiragana.ilike(f"%{query}%")) |
        (JapaneseVocabularyDB.word_romaji.ilike(f"%{query}%")) |
        (JapaneseVocabularyDB.english_meaning.ilike(f"%{query}%"))
    ).limit(20).all()
    
    return results


@router.post("/vocabulary/{vocab_id}/review")
def review_vocabulary(
    vocab_id: uuid.UUID,
    correct: bool,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Record vocabulary review (SRS system)"""
    # Get or create progress record
    progress = db.query(JapaneseVocabProgressDB).filter(
        JapaneseVocabProgressDB.user_id == current_user_id,
        JapaneseVocabProgressDB.vocab_id == vocab_id
    ).first()
    
    if not progress:
        progress = JapaneseVocabProgressDB(
            user_id=current_user_id,
            vocab_id=vocab_id
        )
        db.add(progress)
    
    # Update progress
    progress.times_reviewed += 1
    if correct:
        progress.times_correct += 1
        progress.srs_level = min(progress.srs_level + 1, 10)
    else:
        progress.times_incorrect += 1
        progress.srs_level = max(progress.srs_level - 1, 1)
    
    progress.last_reviewed_at = datetime.utcnow()
    
    # Calculate next review date (SRS intervals)
    srs_intervals = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30, 6: 60, 7: 120, 8: 180, 9: 365, 10: 730}
    days_until_next = srs_intervals.get(progress.srs_level, 1)
    
    from datetime import timedelta
    progress.next_review_date = datetime.utcnow() + timedelta(days=days_until_next)
    
    if progress.srs_level >= 8:
        progress.is_mastered = True
    
    db.commit()
    
    return {
        "correct": correct,
        "srs_level": progress.srs_level,
        "next_review_date": progress.next_review_date,
        "is_mastered": progress.is_mastered
    }


# ==================== KANJI ENDPOINTS ====================

@router.get("/kanji/level/{level}", response_model=List[KanjiResponse])
def get_kanji_by_level(
    level: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get kanji characters by JLPT level"""
    kanji = db.query(JapaneseKanjiDB).filter(
        JapaneseKanjiDB.jlpt_level == level.upper()
    ).order_by(JapaneseKanjiDB.frequency_rank).limit(limit).all()
    
    return kanji


@router.get("/kanji/{kanji_id}")
def get_kanji_details(kanji_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get detailed kanji information"""
    kanji = db.query(JapaneseKanjiDB).filter(
        JapaneseKanjiDB.kanji_id == kanji_id
    ).first()
    
    if not kanji:
        raise HTTPException(status_code=404, detail="Kanji not found")
    
    return kanji


@router.post("/kanji/{kanji_id}/practice")
def practice_kanji(
    kanji_id: uuid.UUID,
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Record kanji practice session"""
    # Get or create progress
    progress = db.query(JapaneseKanjiProgressDB).filter(
        JapaneseKanjiProgressDB.user_id == current_user_id,
        JapaneseKanjiProgressDB.kanji_id == kanji_id
    ).first()
    
    if not progress:
        progress = JapaneseKanjiProgressDB(
            user_id=current_user_id,
            kanji_id=kanji_id
        )
        db.add(progress)
    
    progress.times_practiced = (progress.times_practiced or 0) + 1
    progress.last_practiced_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Practice recorded", "times_practiced": progress.times_practiced}


# ==================== QUIZ ENDPOINTS ====================

@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get quiz details and questions"""
    quiz = db.query(JapaneseQuizDB).filter(
        JapaneseQuizDB.quiz_id == quiz_id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return quiz


@router.post("/quizzes/{quiz_id}/attempt", response_model=QuizAttemptResponse)
def start_quiz_attempt(
    quiz_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Start a new quiz attempt"""
    quiz = db.query(JapaneseQuizDB).filter(
        JapaneseQuizDB.quiz_id == quiz_id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Count previous attempts
    attempt_count = db.query(JapaneseQuizAttemptDB).filter(
        JapaneseQuizAttemptDB.enrollment_id == enrollment_id,
        JapaneseQuizAttemptDB.quiz_id == quiz_id
    ).count()
    
    # Create attempt
    attempt = JapaneseQuizAttemptDB(
        enrollment_id=enrollment_id,
        quiz_id=quiz_id,
        attempt_number=attempt_count + 1
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return attempt


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_quiz(
    quiz_id: uuid.UUID,
    attempt_data: QuizAttemptCreate,
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results"""
    quiz = db.query(JapaneseQuizDB).filter(
        JapaneseQuizDB.quiz_id == quiz_id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # TODO: Implement auto-grading logic
    # For now, return mock results
    
    return {
        "attempt_id": uuid.uuid4(),
        "quiz_id": quiz_id,
        "score": Decimal("85.50"),
        "passed": True,
        "feedback": {"message": "Good job!"}
    }


# ==================== PROGRESS ENDPOINTS ====================

@router.get("/progress/overview", response_model=ProgressResponse)
def get_progress_overview(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get overall learning progress"""
    # Get current enrollment
    enrollment = db.query(JapaneseEnrollmentDB).filter(
        JapaneseEnrollmentDB.user_id == current_user_id,
        JapaneseEnrollmentDB.status == "active"
    ).first()
    
    # Count mastered vocab and kanji
    vocab_mastered = db.query(JapaneseVocabProgressDB).filter(
        JapaneseVocabProgressDB.user_id == current_user_id,
        JapaneseVocabProgressDB.is_mastered == True
    ).count()
    
    kanji_mastered = db.query(JapaneseKanjiProgressDB).filter(
        JapaneseKanjiProgressDB.user_id == current_user_id,
        JapaneseKanjiProgressDB.is_mastered == True
    ).count()
    
    # Get study streak
    streak = db.query(JapaneseStudyStreakDB).filter(
        JapaneseStudyStreakDB.user_id == current_user_id
    ).first()
    
    return {
        "progress_percentage": enrollment.progress_percentage if enrollment else Decimal("0"),
        "current_week": enrollment.current_week if enrollment else 1,
        "total_study_minutes": streak.total_study_minutes if streak else 0,
        "vocabulary_mastered": vocab_mastered,
        "kanji_mastered": kanji_mastered,
        "current_streak_days": streak.current_streak_days if streak else 0
    }


# ==================== SRS ENDPOINTS ====================

@router.get("/srs/due-reviews")
def get_due_reviews(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get vocabulary due for review (SRS)"""
    now = datetime.utcnow()
    
    due_vocab = db.query(JapaneseVocabProgressDB).filter(
        JapaneseVocabProgressDB.user_id == current_user_id,
        JapaneseVocabProgressDB.next_review_date <= now,
        JapaneseVocabProgressDB.is_mastered == False
    ).all()
    
    return {
        "due_count": len(due_vocab),
        "reviews": [
            {
                "vocab_progress_id": str(vp.vocab_progress_id),
                "vocab_id": str(vp.vocab_id),
                "srs_level": vp.srs_level,
                "times_reviewed": vp.times_reviewed
            }
            for vp in due_vocab
        ]
    }


# ==================== CERTIFICATE ENDPOINTS ====================

@router.get("/certificates/my-certs")
def get_my_certificates(
    current_user_id: str = "user_001",  # TODO: Get from auth
    db: Session = Depends(get_db)
):
    """Get user's earned certificates"""
    certs = db.query(JapaneseCertificateDB).filter(
        JapaneseCertificateDB.user_id == current_user_id
    ).all()
    
    return certs


@router.get("/certificates/{certificate_id}/verify")
def verify_certificate(certificate_id: uuid.UUID, db: Session = Depends(get_db)):
    """Verify certificate authenticity (public endpoint)"""
    cert = db.query(JapaneseCertificateDB).filter(
        JapaneseCertificateDB.certificate_id == certificate_id
    ).first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {
        "valid": True,
        "jlpt_level": cert.jlpt_level,
        "certificate_type": cert.certificate_type,
        "issued_at": cert.issued_at,
        "verification_code": cert.verification_code
    }


# ==================== HEALTH CHECK ====================

@router.get("/health")
def japanese_training_health():
    """Health check for Japanese training module"""
    return {
        "status": "healthy",
        "module": "Japanese Language Training",
        "version": "1.0.0"
    }
