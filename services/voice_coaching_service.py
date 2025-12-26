"""
Voice Coaching Service
Business logic for voice coaching sessions with Standard and Realtime modes
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional, Dict, List
import uuid
from datetime import datetime
import os
import openai
from dotenv import load_dotenv

from db_models.wallet import (
    VoiceCoachingSession,
    SessionStatus
)
from services.wallet_service import WalletService
from config.costs import (
    VOICE_COACHING_STANDARD_COST_PER_MINUTE,
    VOICE_COACHING_REALTIME_COST_PER_MINUTE,
    MIN_VOICE_SESSION_DURATION,
    MAX_VOICE_SESSION_DURATION
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class VoiceCoachingService:
    """Service for managing voice coaching sessions"""
    
    # Socratic prompts for different tracks
    SOCRATIC_PROMPTS = {
        "caregiving": """You are a Socratic voice coach specializing in caregiving for Japan-bound workers.
Your role is to help students practice Japanese conversation through guided questioning, not direct answers.
Use the Socratic method: ask thoughtful questions that help students discover answers themselves.
Focus on:
- Patient care vocabulary and phrases
- Medical terminology
- Daily care routines
- Emergency situations
- Cultural sensitivity in healthcare settings
Keep responses concise (2-3 sentences max) and encourage the student to think and respond.""",
        
        "academic": """You are a Socratic voice coach specializing in academic Japanese for students.
Your role is to help students practice Japanese conversation through guided questioning, not direct answers.
Use the Socratic method: ask thoughtful questions that help students discover answers themselves.
Focus on:
- Academic vocabulary and formal language
- Classroom interactions
- Research and study terminology
- Presentation skills
- Academic writing conventions
Keep responses concise (2-3 sentences max) and encourage the student to think and respond.""",
        
        "food_tech": """You are a Socratic voice coach specializing in food technology Japanese.
Your role is to help students practice Japanese conversation through guided questioning, not direct answers.
Use the Socratic method: ask thoughtful questions that help students discover answers themselves.
Focus on:
- Food preparation terminology
- Kitchen equipment and procedures
- Food safety regulations
- Menu planning and descriptions
- Customer service in food industry
Keep responses concise (2-3 sentences max) and encourage the student to think and respond."""
    }
    
    @staticmethod
    def calculate_cost(mode: str, duration_minutes: int) -> Decimal:
        """
        Calculate cost for a voice coaching session
        
        Args:
            mode: 'standard' or 'realtime'
            duration_minutes: Estimated duration in minutes
            
        Returns:
            Cost in NPR
        """
        if mode.lower() == "standard":
            return VOICE_COACHING_STANDARD_COST_PER_MINUTE * Decimal(str(duration_minutes))
        elif mode.lower() == "realtime":
            return VOICE_COACHING_REALTIME_COST_PER_MINUTE * Decimal(str(duration_minutes))
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'standard' or 'realtime'")
    
    @staticmethod
    def get_socratic_prompt(track: str) -> str:
        """
        Get specialized Socratic prompt for a track
        
        Args:
            track: 'caregiving', 'academic', or 'food_tech'
            
        Returns:
            Prompt string
        """
        return VoiceCoachingService.SOCRATIC_PROMPTS.get(
            track.lower(),
            VoiceCoachingService.SOCRATIC_PROMPTS["caregiving"]  # Default
        )
    
    @staticmethod
    def start_session(
        db: Session,
        user_id: str,
        mode: str,
        track: str,
        language: str,
        estimated_duration_minutes: int
    ) -> Dict:
        """
        Start a voice coaching session
        
        Checks balance, reserves funds, and creates session record
        
        Args:
            db: Database session
            user_id: User ID
            mode: 'standard' or 'realtime'
            track: 'caregiving', 'academic', or 'food_tech'
            language: Language code (en, ne, ja)
            estimated_duration_minutes: Estimated session duration
            
        Returns:
            dict with session_id, reserved_amount, and session details
            
        Raises:
            ValueError: If insufficient balance or invalid parameters
        """
        # Validate duration
        if estimated_duration_minutes < MIN_VOICE_SESSION_DURATION:
            raise ValueError(f"Duration must be at least {MIN_VOICE_SESSION_DURATION} minutes")
        if estimated_duration_minutes > MAX_VOICE_SESSION_DURATION:
            raise ValueError(f"Duration must not exceed {MAX_VOICE_SESSION_DURATION} minutes")
        
        # Validate mode
        if mode.lower() not in ["standard", "realtime"]:
            raise ValueError("Mode must be 'standard' or 'realtime'")
        
        # Calculate cost
        estimated_cost = VoiceCoachingService.calculate_cost(mode, estimated_duration_minutes)
        
        # Create session record
        session_id = uuid.uuid4()
        session = VoiceCoachingSession(
            session_id=session_id,
            user_id=user_id,
            mode=mode.lower(),
            duration_minutes=estimated_duration_minutes,
            cost=estimated_cost,
            status=SessionStatus.reserved.value,
            reserved_at=datetime.utcnow(),
            metadata={
                "track": track,
                "language": language,
                "estimated_duration_minutes": estimated_duration_minutes
            }
        )
        db.add(session)
        db.flush()  # Flush to get session_id
        
        # Reserve balance
        try:
            transaction = WalletService.reserve_balance(
                db=db,
                user_id=user_id,
                amount=estimated_cost,
                session_id=session_id,
                description=f"Reserved {estimated_cost} NPR for {mode} voice coaching session"
            )
            
            session.transaction_id = transaction.transaction_id
            db.commit()
            db.refresh(session)
            
            return {
                "session_id": str(session_id),
                "mode": mode.lower(),
                "track": track,
                "language": language,
                "estimated_duration_minutes": estimated_duration_minutes,
                "reserved_amount": float(estimated_cost),
                "status": session.status,
                "reserved_at": session.reserved_at.isoformat() if session.reserved_at else None
            }
            
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Insufficient balance: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Error starting session: {str(e)}")
    
    @staticmethod
    async def handle_standard_mode(
        session_id: uuid.UUID,
        audio_input: Optional[bytes],
        text_input: Optional[str],
        track: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """
        Handle standard mode coaching (Whisper → GPT-4 → TTS pipeline)
        
        For now, uses GPT-4 text completion directly (Whisper/TTS to be added later)
        
        Args:
            session_id: Session ID
            audio_input: Optional audio bytes (not yet processed)
            text_input: Optional text input
            track: Track type (caregiving, academic, food_tech)
            conversation_history: Optional conversation history
            
        Returns:
            dict with response_text and tokens_used
        """
        # Get Socratic prompt for track
        system_prompt = VoiceCoachingService.get_socratic_prompt(track)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user input
        user_input = text_input
        if audio_input and not text_input:
            # TODO: Process audio with Whisper API
            # For now, use placeholder
            user_input = "[Audio input - Whisper processing not yet implemented]"
        
        if not user_input:
            raise ValueError("Either audio_input or text_input must be provided")
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Call GPT-4
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # TODO: Convert response to audio using TTS API
            # For now, return text only
            
            return {
                "response_text": response_text,
                "tokens_used": tokens_used,
                "audio_url": None  # Will be added when TTS is implemented
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    @staticmethod
    async def handle_realtime_mode(
        session_id: uuid.UUID,
        audio_input: Optional[bytes],
        text_input: Optional[str],
        track: str
    ) -> Dict:
        """
        Handle realtime mode coaching
        
        Args:
            session_id: Session ID
            audio_input: Optional audio bytes
            text_input: Optional text input
            track: Track type
            
        Returns:
            dict with response (placeholder for now)
        """
        # Realtime mode not yet implemented
        return {
            "response_text": "Realtime mode is not yet implemented. Please use Standard mode.",
            "tokens_used": 0,
            "audio_url": None
        }
    
    @staticmethod
    def end_session(
        db: Session,
        session_id: uuid.UUID,
        user_id: str,
        actual_duration_minutes: int
    ) -> Dict:
        """
        End a voice coaching session
        
        Calculates actual cost, processes refund if needed, and updates session status
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            actual_duration_minutes: Actual session duration
            
        Returns:
            dict with final cost, refund amount, and session status
        """
        # Get session
        session = db.query(VoiceCoachingSession).filter(
            VoiceCoachingSession.session_id == session_id,
            VoiceCoachingSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.reserved.value and session.status != SessionStatus.active.value:
            raise ValueError(f"Session is in {session.status} status and cannot be ended")
        
        # Calculate actual cost
        actual_cost = VoiceCoachingService.calculate_cost(session.mode, actual_duration_minutes)
        reserved_amount = session.cost
        
        # Finalize reservation and charge actual amount
        try:
            charge_transaction = WalletService.finalize_reservation(
                db=db,
                user_id=user_id,
                reserved_amount=reserved_amount,
                actual_amount=actual_cost,
                session_id=session_id
            )
            
            # Calculate refund if actual cost is less than reserved
            refund_amount = Decimal("0.00")
            if actual_cost < reserved_amount:
                refund_amount = reserved_amount - actual_cost
                WalletService.refund(
                    db=db,
                    user_id=user_id,
                    amount=refund_amount,
                    session_id=session_id,
                    description=f"Refund for unused time: {refund_amount} NPR"
                )
            
            # Update session
            session.status = SessionStatus.completed.value
            session.completed_at = datetime.utcnow()
            session.duration_minutes = actual_duration_minutes
            session.cost = actual_cost
            session.transaction_id = charge_transaction.transaction_id
            
            db.commit()
            db.refresh(session)
            
            return {
                "session_id": str(session_id),
                "status": session.status,
                "reserved_amount": float(reserved_amount),
                "actual_cost": float(actual_cost),
                "refund_amount": float(refund_amount),
                "actual_duration_minutes": actual_duration_minutes,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            }
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error ending session: {str(e)}")

