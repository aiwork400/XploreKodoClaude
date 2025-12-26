"""
Assessment API
Endpoints for evaluating student answers and retrieving assessment results
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from config.database import get_db
from config.dependencies import get_current_user
from db_models.wallet import AssessmentResult
from services.assessment_service import AssessmentService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/coaching/assessment", tags=["Assessment"])


# ==================== PYDANTIC SCHEMAS ====================

class EvaluateAnswerRequest(BaseModel):
    """Evaluate answer request model"""
    question_id: str = Field(..., description="Question identifier")
    student_answer: str = Field(..., description="Student's answer to evaluate")
    track: str = Field(..., pattern="^(caregiving|academic|food_tech)$", description="Track context")
    expected_keigo_level: str = Field(..., description="Expected keigo level (teineigo, sonkeigo, kenjougo)")
    question_text: Optional[str] = Field(None, description="Original question text")
    question_type: Optional[str] = Field("general", description="Question type")
    session_id: Optional[str] = Field(None, description="Optional session ID to link assessment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q1",
                "student_answer": "患者さんに水が必要です",
                "track": "caregiving",
                "expected_keigo_level": "teineigo",
                "question_text": "How do you say 'The patient needs water' in Japanese?",
                "question_type": "keigo_check"
            }
        }


class EvaluateAnswerResponse(BaseModel):
    """Evaluate answer response model"""
    question_id: str
    grammar: float
    keigo_appropriateness: float
    contextual_fit: float
    overall_quality: float
    overall: float
    feedback: str
    track: str
    expected_keigo_level: str


class AssessmentResultResponse(BaseModel):
    """Assessment result response model"""
    assessment_id: str
    user_id: str
    session_id: Optional[str] = None
    assessment_type: str
    score: float
    feedback: Optional[str] = None
    details: Optional[dict] = None
    created_at: str
    
    class Config:
        orm_mode = True


# ==================== API ENDPOINTS ====================

@router.post("/evaluate", response_model=EvaluateAnswerResponse)
async def evaluate_answer(
    request: EvaluateAnswerRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Evaluate a student's answer using GPT-4 with rubric-based scoring
    
    Returns scores for:
    - Grammar (0-25 points)
    - Keigo Appropriateness (0-25 points)
    - Contextual Fit (0-25 points)
    - Overall Quality (0-25 points)
    - Overall Score (0-100 points)
    
    Also provides AI-generated feedback.
    """
    try:
        assessment_result = await AssessmentService.evaluate_answer(
            question_id=request.question_id,
            student_answer=request.student_answer,
            track=request.track,
            expected_keigo_level=request.expected_keigo_level,
            question_text=request.question_text or "",
            question_type=request.question_type or "general"
        )
        
        # Save assessment result to database if session_id provided
        if request.session_id:
            try:
                session_uuid = uuid.UUID(request.session_id)
                assessment_record = AssessmentResult(
                    assessment_id=uuid.uuid4(),
                    user_id=current_user["user_id"],
                    session_id=session_uuid,
                    assessment_type=request.question_type or "general",
                    score=assessment_result["overall"],
                    feedback=assessment_result["feedback"],
                    details={
                        "grammar": assessment_result["grammar"],
                        "keigo_appropriateness": assessment_result["keigo_appropriateness"],
                        "contextual_fit": assessment_result["contextual_fit"],
                        "overall_quality": assessment_result["overall_quality"],
                        "question_id": request.question_id,
                        "track": request.track,
                        "expected_keigo_level": request.expected_keigo_level
                    }
                )
                db.add(assessment_record)
                db.commit()
            except Exception:
                db.rollback()
                # Continue even if saving fails
        
        return EvaluateAnswerResponse(**assessment_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating answer: {str(e)}"
        )


@router.get("/results", response_model=List[AssessmentResultResponse])
async def get_assessment_results(
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's assessment history
    
    - **limit**: Number of results to return (1-100, default: 50)
    - **offset**: Number of results to skip (default: 0)
    - **assessment_type**: Optional filter by type
    - **session_id**: Optional filter by session ID
    
    Returns list of assessments ordered by created_at descending
    """
    try:
        # Build query
        query = db.query(AssessmentResult).filter(
            AssessmentResult.user_id == current_user["user_id"]
        )
        
        # Apply filters
        if assessment_type:
            query = query.filter(AssessmentResult.assessment_type == assessment_type)
        
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
                query = query.filter(AssessmentResult.session_id == session_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session_id format"
                )
        
        # Order by created_at descending and apply pagination
        assessments = query.order_by(
            AssessmentResult.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            AssessmentResultResponse(
                assessment_id=str(a.assessment_id),
                user_id=a.user_id,
                session_id=str(a.session_id) if a.session_id else None,
                assessment_type=a.assessment_type,
                score=float(a.score),
                feedback=a.feedback,
                details=a.details,
                created_at=a.created_at.isoformat() if a.created_at else ""
            )
            for a in assessments
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assessment results: {str(e)}"
        )

