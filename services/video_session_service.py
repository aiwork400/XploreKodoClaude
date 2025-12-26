"""
Video Session Service
Business logic for video sessions with timeline events and interactions
"""
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional, Dict, List
import uuid
from datetime import datetime

from db_models.wallet import (
    VideoSession,
    SessionStatus
)
from services.wallet_service import WalletService
from services.assessment_service import AssessmentService
from config.costs import (
    VIDEO_SESSION_COST_PER_MINUTE,
    MIN_VIDEO_SESSION_DURATION,
    MAX_VIDEO_SESSION_DURATION
)


class VideoSessionService:
    """Service for managing video sessions with timeline events"""
    
    # Video metadata storage (in production, this would be in a database table)
    VIDEO_METADATA = {
        "caregiving_n5_lesson_01_ja": {
            "video_id": "caregiving_n5_lesson_01_ja",
            "title": "Caregiving Basics - N5 Lesson 1",
            "track": "caregiving",
            "language": "ja",
            "duration_minutes": 20,
            "video_url": "/videos/caregiving/n5_lesson_01_ja.mp4",
            "timeline_events": [
                {
                    "event_id": "q1",
                    "timestamp": 120,  # seconds
                    "type": "question",
                    "question_text": "How do you say 'The patient needs water' in Japanese?",
                    "question_type": "keigo_check",
                    "expected_keigo_level": "teineigo",
                    "options": None
                },
                {
                    "event_id": "practice_1",
                    "timestamp": 300,
                    "type": "practice_prompt",
                    "prompt_text": "Practice saying: 'お水をください' (Please give me water)",
                    "practice_type": "pronunciation"
                },
                {
                    "event_id": "q2",
                    "timestamp": 600,
                    "type": "question",
                    "question_text": "What is the polite form of '食べる' (to eat)?",
                    "question_type": "grammar",
                    "expected_keigo_level": "teineigo",
                    "options": ["食べます", "食べる", "食べて", "食べた"]
                }
            ]
        },
        "academic_n4_lesson_02_ja": {
            "video_id": "academic_n4_lesson_02_ja",
            "title": "Academic Japanese - N4 Lesson 2",
            "track": "academic",
            "language": "ja",
            "duration_minutes": 25,
            "video_url": "/videos/academic/n4_lesson_02_ja.mp4",
            "timeline_events": [
                {
                    "event_id": "q1",
                    "timestamp": 180,
                    "type": "question",
                    "question_text": "How would you politely ask a professor: 'May I ask a question?'",
                    "question_type": "keigo_check",
                    "expected_keigo_level": "sonkeigo",
                    "options": None
                }
            ]
        },
        "food_tech_n5_lesson_01_ja": {
            "video_id": "food_tech_n5_lesson_01_ja",
            "title": "Food Technology Basics - N5 Lesson 1",
            "track": "food_tech",
            "language": "ja",
            "duration_minutes": 18,
            "video_url": "/videos/food_tech/n5_lesson_01_ja.mp4",
            "timeline_events": [
                {
                    "event_id": "q1",
                    "timestamp": 150,
                    "type": "question",
                    "question_text": "How do you say 'The kitchen is clean' in Japanese?",
                    "question_type": "vocabulary",
                    "expected_keigo_level": "teineigo",
                    "options": None
                }
            ]
        }
    }
    
    @staticmethod
    def get_video_metadata(video_id: str) -> Optional[Dict]:
        """
        Get video metadata including timeline events
        
        Args:
            video_id: Video identifier
            
        Returns:
            dict with video metadata and timeline events, or None if not found
        """
        return VideoSessionService.VIDEO_METADATA.get(video_id)
    
    @staticmethod
    def start_session(
        db: Session,
        user_id: str,
        video_id: str,
        language: str
    ) -> Dict:
        """
        Start a video session
        
        Creates session record, reserves balance, and returns video URL with timeline events
        
        Args:
            db: Database session
            user_id: User ID
            video_id: Video identifier
            language: Language code
            
        Returns:
            dict with session_id, video_url, timeline_events, and session details
            
        Raises:
            ValueError: If video not found or insufficient balance
        """
        # Get video metadata
        metadata = VideoSessionService.get_video_metadata(video_id)
        if not metadata:
            raise ValueError(f"Video {video_id} not found")
        
        # Calculate cost
        duration_minutes = metadata["duration_minutes"]
        estimated_cost = VIDEO_SESSION_COST_PER_MINUTE * Decimal(str(duration_minutes))
        
        # Create session record
        session_id = uuid.uuid4()
        session = VideoSession(
            session_id=session_id,
            user_id=user_id,
            duration_minutes=duration_minutes,
            cost=estimated_cost,
            status=SessionStatus.reserved.value,
            reserved_at=datetime.utcnow(),
            video_session_metadata={
                "video_id": video_id,
                "language": language,
                "track": metadata["track"],
                "title": metadata["title"],
                "timeline_events": metadata["timeline_events"],
                "answers": {},  # Store answers by question_id
                "progress": {
                    "current_timestamp": 0,
                    "completion_percentage": 0.0
                }
            }
        )
        db.add(session)
        db.flush()
        
        # Reserve balance
        try:
            transaction = WalletService.reserve_balance(
                db=db,
                user_id=user_id,
                amount=estimated_cost,
                session_id=session_id,
                description=f"Reserved {estimated_cost} NPR for video session"
            )
            
            session.transaction_id = transaction.transaction_id
            db.commit()
            db.refresh(session)
            
            return {
                "session_id": str(session_id),
                "video_id": video_id,
                "video_url": metadata["video_url"],
                "title": metadata["title"],
                "track": metadata["track"],
                "language": language,
                "duration_minutes": duration_minutes,
                "timeline_events": metadata["timeline_events"],
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
    async def answer_question(
        db: Session,
        session_id: uuid.UUID,
        user_id: str,
        question_id: str,
        answer: str,
        answer_mode: str = "text"
    ) -> Dict:
        """
        Answer a timeline question
        
        Saves answer and calls assessment service
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            question_id: Question event ID
            answer: Student's answer
            answer_mode: 'text' or 'audio' (for future use)
            
        Returns:
            dict with assessment results
        """
        # Get session
        session = db.query(VideoSession).filter(
            VideoSession.session_id == session_id,
            VideoSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status not in ["reserved", "active"]:
            raise ValueError(f"Session is in {session.status} status and cannot receive answers")
        
        # Update session to active if needed
        if session.status == "reserved":
            session.status = "active"
            session.started_at = datetime.utcnow()
        
        # Get question from timeline events
        timeline_events = session.video_session_metadata.get("timeline_events", [])
        question = next((e for e in timeline_events if e.get("event_id") == question_id), None)
        
        if not question:
            raise ValueError(f"Question {question_id} not found in timeline")
        
        if question.get("type") != "question":
            raise ValueError(f"Event {question_id} is not a question")
        
        # Get track and expected keigo level
        track = session.video_session_metadata.get("track", "caregiving")
        expected_keigo_level = question.get("expected_keigo_level", "teineigo")
        
        # Call assessment service
        assessment_result = AssessmentService.evaluate_answer(
            question_id=question_id,
            student_answer=answer,
            track=track,
            expected_keigo_level=expected_keigo_level,
            question_text=question.get("question_text", ""),
            question_type=question.get("question_type", "general")
        )
        
        # Save answer in session metadata
        if "answers" not in session.video_session_metadata:
            session.video_session_metadata["answers"] = {}
        
        session.video_session_metadata["answers"][question_id] = {
            "answer": answer,
            "answer_mode": answer_mode,
            "answered_at": datetime.utcnow().isoformat(),
            "assessment": assessment_result
        }
        
        db.commit()
        db.refresh(session)
        
        return {
            "question_id": question_id,
            "answer": answer,
            "assessment": assessment_result,
            "session_id": str(session_id)
        }
    
    @staticmethod
    def update_progress(
        db: Session,
        session_id: uuid.UUID,
        user_id: str,
        current_timestamp: int,
        completion_percentage: float
    ) -> Dict:
        """
        Update viewing progress
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            current_timestamp: Current playback timestamp in seconds
            completion_percentage: Completion percentage (0-100)
            
        Returns:
            dict with updated progress
        """
        session = db.query(VideoSession).filter(
            VideoSession.session_id == session_id,
            VideoSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Update progress in metadata
        if "progress" not in session.video_session_metadata:
            session.video_session_metadata["progress"] = {}
        
        session.video_session_metadata["progress"]["current_timestamp"] = current_timestamp
        session.video_session_metadata["progress"]["completion_percentage"] = completion_percentage
        session.video_session_metadata["progress"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Update session status to active if not already
        if session.status == "reserved":
            session.status = "active"
            session.started_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        return {
            "session_id": str(session_id),
            "current_timestamp": current_timestamp,
            "completion_percentage": completion_percentage
        }
    
    @staticmethod
    def complete_session(
        db: Session,
        session_id: uuid.UUID,
        user_id: str
    ) -> Dict:
        """
        Complete a video session
        
        Marks session as completed and finalizes payment
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            
        Returns:
            dict with completion details
        """
        session = db.query(VideoSession).filter(
            VideoSession.session_id == session_id,
            VideoSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status == "completed":
            raise ValueError("Session is already completed")
        
        # Get actual duration from progress
        progress = session.video_session_metadata.get("progress", {})
        completion_percentage = progress.get("completion_percentage", 100.0)
        
        # Calculate actual cost (proportional to completion)
        actual_duration_minutes = (session.duration_minutes * Decimal(str(completion_percentage))) / Decimal("100.00")
        actual_cost = VIDEO_SESSION_COST_PER_MINUTE * actual_duration_minutes
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
                    description=f"Refund for incomplete video session: {refund_amount} NPR"
                )
            
            # Update session
            session.status = SessionStatus.completed.value
            session.completed_at = datetime.utcnow()
            session.transaction_id = charge_transaction.transaction_id
            
            db.commit()
            db.refresh(session)
            
            return {
                "session_id": str(session_id),
                "status": session.status,
                "reserved_amount": float(reserved_amount),
                "actual_cost": float(actual_cost),
                "refund_amount": float(refund_amount),
                "completion_percentage": completion_percentage,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            }
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Error completing session: {str(e)}")

