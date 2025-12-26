"""
Video Session API
Endpoints for video sessions with timeline events and interactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import uuid

from config.database import get_db
from config.dependencies import get_current_user
from db_models.wallet import VideoSession
from services.video_session_service import VideoSessionService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/coaching/video", tags=["Video Sessions"])


# ==================== PYDANTIC SCHEMAS ====================

class StartVideoSessionRequest(BaseModel):
    """Start video session request model"""
    video_id: str = Field(..., description="Video identifier (e.g., 'caregiving_n5_lesson_01_ja')")
    language: str = Field("ja", description="Language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            }
        }


class StartVideoSessionResponse(BaseModel):
    """Start video session response model"""
    session_id: str
    video_id: str
    video_url: str
    title: str
    track: str
    language: str
    duration_minutes: int
    timeline_events: List[dict]
    reserved_amount: float
    status: str
    reserved_at: Optional[str] = None


class AnswerQuestionRequest(BaseModel):
    """Answer question request model"""
    question_id: str = Field(..., description="Question event ID from timeline")
    answer: str = Field(..., description="Student's answer")
    answer_mode: str = Field("text", pattern="^(text|audio)$", description="Answer mode: text or audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q1",
                "answer": "患者さんに水が必要です",
                "answer_mode": "text"
            }
        }


class AnswerQuestionResponse(BaseModel):
    """Answer question response model"""
    question_id: str
    answer: str
    assessment: dict
    session_id: str


class UpdateProgressRequest(BaseModel):
    """Update progress request model"""
    current_timestamp: int = Field(..., ge=0, description="Current playback timestamp in seconds")
    completion_percentage: float = Field(..., ge=0, le=100, description="Completion percentage (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_timestamp": 300,
                "completion_percentage": 25.0
            }
        }


class UpdateProgressResponse(BaseModel):
    """Update progress response model"""
    session_id: str
    current_timestamp: int
    completion_percentage: float


class CompleteSessionResponse(BaseModel):
    """Complete session response model"""
    session_id: str
    status: str
    reserved_amount: float
    actual_cost: float
    refund_amount: float
    completion_percentage: float
    completed_at: Optional[str] = None


class VideoSessionResponse(BaseModel):
    """Video session list response model"""
    session_id: str
    video_id: str
    title: str
    track: str
    language: str
    duration_minutes: int
    status: str
    completion_percentage: float
    created_at: str
    
    class Config:
        orm_mode = True


# ==================== API ENDPOINTS ====================

@router.post("/start", response_model=StartVideoSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_video_session(
    request: StartVideoSessionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Start a video session
    
    - Checks user balance
    - Reserves funds for video duration
    - Creates session record
    - Returns video URL and timeline events
    
    Video cost: NPR 15.00 per minute
    """
    try:
        result = VideoSessionService.start_session(
            db=db,
            user_id=current_user["user_id"],
            video_id=request.video_id,
            language=request.language
        )
        
        return StartVideoSessionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting session: {str(e)}"
        )


@router.post("/{session_id}/answer-question", response_model=AnswerQuestionResponse)
async def answer_question(
    session_id: str,
    request: AnswerQuestionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Answer a timeline question
    
    - **session_id**: Session ID from /start endpoint
    - **question_id**: Question event ID from timeline
    - **answer**: Student's answer
    - **answer_mode**: 'text' or 'audio'
    
    Returns assessment results with rubric scores
    """
    try:
        session_uuid = uuid.UUID(session_id)
        
        result = await VideoSessionService.answer_question(
            db=db,
            session_id=session_uuid,
            user_id=current_user["user_id"],
            question_id=request.question_id,
            answer=request.answer,
            answer_mode=request.answer_mode
        )
        
        return AnswerQuestionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing answer: {str(e)}"
        )


@router.post("/{session_id}/progress", response_model=UpdateProgressResponse)
async def update_progress(
    session_id: str,
    request: UpdateProgressRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update video viewing progress
    
    - **session_id**: Session ID
    - **current_timestamp**: Current playback timestamp in seconds
    - **completion_percentage**: Completion percentage (0-100)
    """
    try:
        session_uuid = uuid.UUID(session_id)
        
        result = VideoSessionService.update_progress(
            db=db,
            session_id=session_uuid,
            user_id=current_user["user_id"],
            current_timestamp=request.current_timestamp,
            completion_percentage=request.completion_percentage
        )
        
        return UpdateProgressResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating progress: {str(e)}"
        )


@router.post("/{session_id}/complete", response_model=CompleteSessionResponse)
async def complete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Complete a video session
    
    - Calculates actual cost based on completion percentage
    - Processes refund if session not fully completed
    - Marks session as completed
    """
    try:
        session_uuid = uuid.UUID(session_id)
        
        result = VideoSessionService.complete_session(
            db=db,
            session_id=session_uuid,
            user_id=current_user["user_id"]
        )
        
        return CompleteSessionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing session: {str(e)}"
        )


@router.get("/sessions", response_model=List[VideoSessionResponse])
async def get_user_sessions(
    limit: int = Query(50, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's video sessions
    
    - **limit**: Number of sessions to return (1-100, default: 50)
    - **offset**: Number of sessions to skip (default: 0)
    - **status_filter**: Optional filter by status (reserved, active, completed, cancelled)
    
    Returns list of sessions ordered by created_at descending
    """
    try:
        # Build query
        query = db.query(VideoSession).filter(
            VideoSession.user_id == current_user["user_id"]
        )
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(VideoSession.status == status_filter)
        
        # Order by created_at descending and apply pagination
        sessions = query.order_by(
            VideoSession.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            VideoSessionResponse(
                session_id=str(s.session_id),
                video_id=s.video_session_metadata.get("video_id", ""),
                title=s.video_session_metadata.get("title", ""),
                track=s.video_session_metadata.get("track", ""),
                language=s.video_session_metadata.get("language", ""),
                duration_minutes=s.duration_minutes,
                status=s.status,
                completion_percentage=s.video_session_metadata.get("progress", {}).get("completion_percentage", 0.0),
                created_at=s.created_at.isoformat() if s.created_at else ""
            )
            for s in sessions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sessions: {str(e)}"
        )

