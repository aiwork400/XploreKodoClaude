"""
Video Session Tests
Tests for video session service and API endpoints
"""
from fastapi.testclient import TestClient
import pytest
from decimal import Decimal
from unittest.mock import patch

from services.video_session_service import VideoSessionService
from services.wallet_service import WalletService
from config.costs import VIDEO_SESSION_COST_PER_MINUTE


class TestVideoSessionService:
    """Test video session service methods"""
    
    def test_get_video_metadata(self):
        """Test retrieving video metadata"""
        metadata = VideoSessionService.get_video_metadata("caregiving_n5_lesson_01_ja")
        
        assert metadata is not None
        assert metadata["video_id"] == "caregiving_n5_lesson_01_ja"
        assert metadata["track"] == "caregiving"
        assert "timeline_events" in metadata
        assert len(metadata["timeline_events"]) > 0
    
    def test_get_video_metadata_not_found(self):
        """Test retrieving non-existent video metadata"""
        metadata = VideoSessionService.get_video_metadata("nonexistent_video")
        
        assert metadata is None
    
    def test_start_session_insufficient_balance(self, test_db, test_user):
        """Test starting session with insufficient balance"""
        user_id = test_user.user_id
        
        # Ensure wallet has no balance
        wallet = WalletService.get_or_create_wallet(test_db, user_id)
        wallet.balance = Decimal("0.00")
        wallet.reserved_balance = Decimal("0.00")
        test_db.commit()
        
        # Try to start a session
        with pytest.raises(ValueError, match="Insufficient balance"):
            VideoSessionService.start_session(
                db=test_db,
                user_id=user_id,
                video_id="caregiving_n5_lesson_01_ja",
                language="ja"
            )
    
    def test_start_session_success(self, test_db, test_user):
        """Test starting session with sufficient balance"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        result = VideoSessionService.start_session(
            db=test_db,
            user_id=user_id,
            video_id="caregiving_n5_lesson_01_ja",
            language="ja"
        )
        
        assert "session_id" in result
        assert result["video_id"] == "caregiving_n5_lesson_01_ja"
        assert result["track"] == "caregiving"
        assert "timeline_events" in result
        assert len(result["timeline_events"]) > 0
        assert result["reserved_amount"] == 300.0  # 15.00 * 20 minutes
    
    @pytest.mark.asyncio
    async def test_answer_question(self, test_db, test_user):
        """Test answering a timeline question"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_result = VideoSessionService.start_session(
            db=test_db,
            user_id=user_id,
            video_id="caregiving_n5_lesson_01_ja",
            language="ja"
        )
        
        session_id = start_result["session_id"]
        
        # Mock assessment service
        with patch('services.video_session_service.AssessmentService.evaluate_answer') as mock_assess:
            mock_assess.return_value = {
                "question_id": "q1",
                "grammar": 20.0,
                "keigo_appropriateness": 22.0,
                "contextual_fit": 23.0,
                "overall_quality": 21.0,
                "overall": 86.0,
                "feedback": "Good answer!",
                "track": "caregiving",
                "expected_keigo_level": "teineigo"
            }
            
            # Answer question
            result = await VideoSessionService.answer_question(
                db=test_db,
                session_id=session_id,
                user_id=user_id,
                question_id="q1",
                answer="患者さんに水が必要です",
                answer_mode="text"
            )
            
            assert result["question_id"] == "q1"
            assert "assessment" in result
            assert result["assessment"]["overall"] == 86.0
    
    def test_update_progress(self, test_db, test_user):
        """Test updating video viewing progress"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_result = VideoSessionService.start_session(
            db=test_db,
            user_id=user_id,
            video_id="caregiving_n5_lesson_01_ja",
            language="ja"
        )
        
        session_id = start_result["session_id"]
        
        # Update progress
        result = VideoSessionService.update_progress(
            db=test_db,
            session_id=session_id,
            user_id=user_id,
            current_timestamp=300,
            completion_percentage=25.0
        )
        
        assert result["current_timestamp"] == 300
        assert result["completion_percentage"] == 25.0
    
    def test_complete_session(self, test_db, test_user):
        """Test completing a video session"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_result = VideoSessionService.start_session(
            db=test_db,
            user_id=user_id,
            video_id="caregiving_n5_lesson_01_ja",
            language="ja"
        )
        
        session_id = start_result["session_id"]
        
        # Update progress to 50%
        VideoSessionService.update_progress(
            db=test_db,
            session_id=session_id,
            user_id=user_id,
            current_timestamp=600,
            completion_percentage=50.0
        )
        
        # Complete session
        result = VideoSessionService.complete_session(
            db=test_db,
            session_id=session_id,
            user_id=user_id
        )
        
        assert result["status"] == "completed"
        assert result["completion_percentage"] == 50.0
        assert result["actual_cost"] == 150.0  # 50% of 300.00
        assert result["refund_amount"] == 150.0  # Refund for unused portion


class TestVideoSessionAPI:
    """Test video session API endpoints"""
    
    def test_start_video_session_endpoint_insufficient_balance(self, client):
        """Test start session endpoint with insufficient balance"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should fail with insufficient balance
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]
    
    def test_start_video_session_endpoint_success(self, client, test_db):
        """Test start session endpoint with sufficient balance"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video2@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video2@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        response = client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["video_id"] == "caregiving_n5_lesson_01_ja"
        assert "timeline_events" in data
        assert len(data["timeline_events"]) > 0
    
    def test_answer_question_endpoint(self, client, test_db):
        """Test answer question endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video3@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video3@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_response = client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        session_id = start_response.json()["session_id"]
        
        # Mock assessment service (async)
        async def mock_evaluate(*args, **kwargs):
            return {
                "question_id": "q1",
                "grammar": 20.0,
                "keigo_appropriateness": 22.0,
                "contextual_fit": 23.0,
                "overall_quality": 21.0,
                "overall": 86.0,
                "feedback": "Good answer!",
                "track": "caregiving",
                "expected_keigo_level": "teineigo"
            }
        
        with patch('services.video_session_service.AssessmentService.evaluate_answer', side_effect=mock_evaluate):
            # Answer question
            answer_response = client.post(
                f"/api/coaching/video/{session_id}/answer-question",
                json={
                    "question_id": "q1",
                    "answer": "患者さんに水が必要です",
                    "answer_mode": "text"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert answer_response.status_code == 200
            data = answer_response.json()
            assert data["question_id"] == "q1"
            assert "assessment" in data
    
    def test_update_progress_endpoint(self, client, test_db):
        """Test update progress endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video4@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video4@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_response = client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        session_id = start_response.json()["session_id"]
        
        # Update progress
        progress_response = client.post(
            f"/api/coaching/video/{session_id}/progress",
            json={
                "current_timestamp": 300,
                "completion_percentage": 25.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert progress_response.status_code == 200
        data = progress_response.json()
        assert data["current_timestamp"] == 300
        assert data["completion_percentage"] == 25.0
    
    def test_complete_session_endpoint(self, client, test_db):
        """Test complete session endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video5@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video5@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_response = client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        session_id = start_response.json()["session_id"]
        
        # Update progress
        client.post(
            f"/api/coaching/video/{session_id}/progress",
            json={
                "current_timestamp": 600,
                "completion_percentage": 50.0
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Complete session
        complete_response = client.post(
            f"/api/coaching/video/{session_id}/complete",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert complete_response.status_code == 200
        data = complete_response.json()
        assert data["status"] == "completed"
        assert data["completion_percentage"] == 50.0
    
    def test_get_user_sessions_endpoint(self, client, test_db):
        """Test get user sessions endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test_video6@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test_video6@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("500.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start a session
        client.post(
            "/api/coaching/video/start",
            json={
                "video_id": "caregiving_n5_lesson_01_ja",
                "language": "ja"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get sessions
        response = client.get(
            "/api/coaching/video/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["video_id"] == "caregiving_n5_lesson_01_ja"

