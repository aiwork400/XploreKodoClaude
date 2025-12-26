"""
Voice Coaching API
Endpoints for voice coaching sessions with Standard and Realtime modes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
import uuid

from config.database import get_db
from config.dependencies import get_current_user
from services.voice_coaching_service import VoiceCoachingService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/coaching/voice", tags=["Voice Coaching"])


# ==================== PYDANTIC SCHEMAS ====================

class StartSessionRequest(BaseModel):
    """Start session request model"""
    mode: str = Field(..., pattern="^(standard|realtime)$", description="Session mode: standard or realtime")
    track: str = Field(..., description="Track: caregiving, academic, or food_tech")
    language: str = Field("en", description="Language code: en, ne, or ja")
    estimated_duration_minutes: int = Field(..., ge=5, le=60, description="Estimated duration in minutes (5-60)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mode": "standard",
                "track": "caregiving",
                "language": "en",
                "estimated_duration_minutes": 15
            }
        }


class StartSessionResponse(BaseModel):
    """Start session response model"""
    session_id: str
    mode: str
    track: str
    language: str
    estimated_duration_minutes: int
    reserved_amount: float
    status: str
    reserved_at: Optional[str] = None


class MessageRequest(BaseModel):
    """Message request model"""
    text_input: Optional[str] = Field(None, description="Text input (if not using audio)")
    track: str = Field(..., description="Track: caregiving, academic, or food_tech")
    conversation_history: Optional[List[dict]] = Field(None, description="Optional conversation history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text_input": "How do I say 'patient needs water' in Japanese?",
                "track": "caregiving",
                "conversation_history": []
            }
        }


class MessageResponse(BaseModel):
    """Message response model"""
    response_text: str
    tokens_used: int
    audio_url: Optional[str] = None


class EndSessionRequest(BaseModel):
    """End session request model"""
    actual_duration_minutes: int = Field(..., ge=1, description="Actual session duration in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "actual_duration_minutes": 12
            }
        }


class EndSessionResponse(BaseModel):
    """End session response model"""
    session_id: str
    status: str
    reserved_amount: float
    actual_cost: float
    refund_amount: float
    actual_duration_minutes: int
    completed_at: Optional[str] = None


class EstimateCostResponse(BaseModel):
    """Estimate cost response model"""
    mode: str
    duration_minutes: int
    cost_npr: float


# ==================== API ENDPOINTS ====================

@router.post("/start", response_model=StartSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Start a voice coaching session
    
    - Checks user balance
    - Reserves funds for estimated duration
    - Creates session record
    
    Modes:
    - **standard**: NPR 2/min (GPT-4 text completion)
    - **realtime**: NPR 40/min (not yet implemented)
    
    Tracks:
    - **caregiving**: For Japan-bound caregiving workers
    - **academic**: For academic students
    - **food_tech**: For food technology workers
    """
    try:
        result = VoiceCoachingService.start_session(
            db=db,
            user_id=current_user["user_id"],
            mode=request.mode,
            track=request.track,
            language=request.language,
            estimated_duration_minutes=request.estimated_duration_minutes
        )
        
        return StartSessionResponse(**result)
        
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


@router.post("/{session_id}/message", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: MessageRequest,
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message (text or audio) to the voice coaching session
    
    - **session_id**: Session ID from /start endpoint
    - **text_input**: Text input (required if no audio)
    - **audio_file**: Optional audio file (not yet processed with Whisper)
    - **track**: Track type for context
    - **conversation_history**: Optional conversation history
    
    For Standard mode: Uses GPT-4 text completion
    For Realtime mode: Returns "Not yet implemented" placeholder
    """
    try:
        session_uuid = uuid.UUID(session_id)
        
        # Verify session belongs to user
        from db_models.wallet import VoiceCoachingSession
        session = db.query(VoiceCoachingSession).filter(
            VoiceCoachingSession.session_id == session_uuid,
            VoiceCoachingSession.user_id == current_user["user_id"]
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session.status not in ["reserved", "active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session is in {session.status} status and cannot receive messages"
            )
        
        # Update session to active if it's still reserved
        if session.status == "reserved":
            from datetime import datetime
            session.status = "active"
            session.started_at = datetime.utcnow()
            db.commit()
        
        # Read audio file if provided
        audio_input = None
        if audio_file:
            audio_input = await audio_file.read()
        
        # Handle based on mode
        if session.mode == "standard":
            result = await VoiceCoachingService.handle_standard_mode(
                session_id=session_uuid,
                audio_input=audio_input,
                text_input=request.text_input,
                track=request.track,
                conversation_history=request.conversation_history
            )
        elif session.mode == "realtime":
            result = await VoiceCoachingService.handle_realtime_mode(
                session_id=session_uuid,
                audio_input=audio_input,
                text_input=request.text_input,
                track=request.track
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session mode: {session.mode}"
            )
        
        return MessageResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/{session_id}/end", response_model=EndSessionResponse)
async def end_session(
    session_id: str,
    request: EndSessionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    End a voice coaching session
    
    - Calculates actual cost based on actual duration
    - Processes refund if actual cost < reserved amount
    - Updates session status to completed
    
    - **session_id**: Session ID to end
    - **actual_duration_minutes**: Actual session duration
    """
    try:
        session_uuid = uuid.UUID(session_id)
        
        result = VoiceCoachingService.end_session(
            db=db,
            session_id=session_uuid,
            user_id=current_user["user_id"],
            actual_duration_minutes=request.actual_duration_minutes
        )
        
        return EndSessionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ending session: {str(e)}"
        )


@router.get("/estimate-cost", response_model=EstimateCostResponse)
async def estimate_cost(
    mode: str = Query(..., pattern="^(standard|realtime)$", description="Session mode"),
    duration_minutes: int = Query(..., ge=5, le=60, description="Duration in minutes (5-60)")
):
    """
    Estimate cost for a voice coaching session
    
    - **mode**: 'standard' (NPR 2/min) or 'realtime' (NPR 40/min)
    - **duration_minutes**: Estimated duration (5-60 minutes)
    
    Returns estimated cost in NPR
    """
    try:
        cost = VoiceCoachingService.calculate_cost(mode, duration_minutes)
        
        return EstimateCostResponse(
            mode=mode,
            duration_minutes=duration_minutes,
            cost_npr=float(cost)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

