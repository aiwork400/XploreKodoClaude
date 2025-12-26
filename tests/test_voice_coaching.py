"""
Voice Coaching Tests
Tests for voice coaching service and API endpoints
"""
from fastapi.testclient import TestClient
import pytest
from decimal import Decimal

from services.voice_coaching_service import VoiceCoachingService
from services.wallet_service import WalletService
from config.costs import (
    VOICE_COACHING_STANDARD_COST_PER_MINUTE,
    VOICE_COACHING_REALTIME_COST_PER_MINUTE
)


class TestVoiceCoachingCostCalculation:
    """Test cost calculation for voice coaching"""
    
    def test_calculate_standard_mode_cost(self):
        """Test cost calculation for standard mode"""
        duration = 15
        expected_cost = VOICE_COACHING_STANDARD_COST_PER_MINUTE * Decimal(str(duration))
        
        cost = VoiceCoachingService.calculate_cost("standard", duration)
        
        assert cost == expected_cost
        assert cost == Decimal("30.00")  # 2.00 * 15
    
    def test_calculate_realtime_mode_cost(self):
        """Test cost calculation for realtime mode"""
        duration = 10
        expected_cost = VOICE_COACHING_REALTIME_COST_PER_MINUTE * Decimal(str(duration))
        
        cost = VoiceCoachingService.calculate_cost("realtime", duration)
        
        assert cost == expected_cost
        assert cost == Decimal("400.00")  # 40.00 * 10
    
    def test_calculate_cost_invalid_mode(self):
        """Test that invalid mode raises ValueError"""
        with pytest.raises(ValueError, match="Invalid mode"):
            VoiceCoachingService.calculate_cost("invalid", 10)


class TestVoiceCoachingSessionLifecycle:
    """Test voice coaching session lifecycle"""
    
    def test_start_session_insufficient_balance(self, test_db, test_user):
        """Test that starting session with insufficient balance raises error"""
        user_id = test_user.user_id
        
        # Ensure wallet has no balance
        wallet = WalletService.get_or_create_wallet(test_db, user_id)
        wallet.balance = Decimal("0.00")
        wallet.reserved_balance = Decimal("0.00")
        test_db.commit()
        
        # Try to start a session that costs more than balance
        with pytest.raises(ValueError, match="Insufficient balance"):
            VoiceCoachingService.start_session(
                db=test_db,
                user_id=user_id,
                mode="standard",
                track="caregiving",
                language="en",
                estimated_duration_minutes=15
            )
    
    def test_start_session_sufficient_balance(self, test_db, test_user):
        """Test starting session with sufficient balance"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("100.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        result = VoiceCoachingService.start_session(
            db=test_db,
            user_id=user_id,
            mode="standard",
            track="caregiving",
            language="en",
            estimated_duration_minutes=15
        )
        
        assert "session_id" in result
        assert result["mode"] == "standard"
        assert result["track"] == "caregiving"
        assert result["reserved_amount"] == 30.0  # 2.00 * 15
        assert result["status"] == "reserved"
    
    def test_end_session_with_refund(self, test_db, test_user):
        """Test ending session where actual cost < reserved amount (refund scenario)"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("100.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session with 15 minutes estimated
        start_result = VoiceCoachingService.start_session(
            db=test_db,
            user_id=user_id,
            mode="standard",
            track="caregiving",
            language="en",
            estimated_duration_minutes=15
        )
        
        session_id = start_result["session_id"]
        reserved_amount = start_result["reserved_amount"]
        
        # End session with only 10 minutes actual (should get refund)
        end_result = VoiceCoachingService.end_session(
            db=test_db,
            session_id=session_id,
            user_id=user_id,
            actual_duration_minutes=10
        )
        
        assert end_result["status"] == "completed"
        assert end_result["reserved_amount"] == reserved_amount
        assert end_result["actual_cost"] == 20.0  # 2.00 * 10
        assert end_result["refund_amount"] == 10.0  # 30.00 - 20.00
        assert end_result["actual_duration_minutes"] == 10
    
    def test_end_session_no_refund(self, test_db, test_user):
        """Test ending session where actual cost = reserved amount (no refund)"""
        user_id = test_user.user_id
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("100.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session with 15 minutes estimated
        start_result = VoiceCoachingService.start_session(
            db=test_db,
            user_id=user_id,
            mode="standard",
            track="caregiving",
            language="en",
            estimated_duration_minutes=15
        )
        
        session_id = start_result["session_id"]
        
        # End session with exactly 15 minutes (no refund)
        end_result = VoiceCoachingService.end_session(
            db=test_db,
            session_id=session_id,
            user_id=user_id,
            actual_duration_minutes=15
        )
        
        assert end_result["status"] == "completed"
        assert end_result["actual_cost"] == 30.0  # 2.00 * 15
        assert end_result["refund_amount"] == 0.0


class TestVoiceCoachingAPI:
    """Test voice coaching API endpoints"""
    
    def test_estimate_cost_endpoint(self, client):
        """Test estimate cost endpoint"""
        response = client.get(
            "/api/coaching/voice/estimate-cost",
            params={
                "mode": "standard",
                "duration_minutes": 15
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "standard"
        assert data["duration_minutes"] == 15
        assert data["cost_npr"] == 30.0
    
    def test_start_session_endpoint_insufficient_balance(self, client):
        """Test start session endpoint with insufficient balance"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/coaching/voice/start",
            json={
                "mode": "standard",
                "track": "caregiving",
                "language": "en",
                "estimated_duration_minutes": 15
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should fail with insufficient balance
        assert response.status_code == 400
        assert "Insufficient balance" in response.json()["detail"]
    
    def test_start_session_endpoint_success(self, client, test_db):
        """Test start session endpoint with sufficient balance"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test2@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test2@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet first
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("100.00"),
            payment_method_id="test_pm_123"
        )
        
        response = client.post(
            "/api/coaching/voice/start",
            json={
                "mode": "standard",
                "track": "caregiving",
                "language": "en",
                "estimated_duration_minutes": 15
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["mode"] == "standard"
        assert data["reserved_amount"] == 30.0
    
    def test_end_session_endpoint(self, client, test_db):
        """Test end session endpoint"""
        # Register and login
        client.post("/api/auth/register", json={
            "email": "test3@example.com",
            "password": "TestPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "test3@example.com",
            "password": "TestPass123!"
        })
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        
        # Top up wallet
        WalletService.topup(
            db=test_db,
            user_id=user_id,
            amount_npr=Decimal("100.00"),
            payment_method_id="test_pm_123"
        )
        
        # Start session
        start_response = client.post(
            "/api/coaching/voice/start",
            json={
                "mode": "standard",
                "track": "caregiving",
                "language": "en",
                "estimated_duration_minutes": 15
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        session_id = start_response.json()["session_id"]
        
        # End session
        end_response = client.post(
            f"/api/coaching/voice/{session_id}/end",
            json={
                "actual_duration_minutes": 10
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert end_response.status_code == 200
        data = end_response.json()
        assert data["status"] == "completed"
        assert data["actual_cost"] == 20.0
        assert data["refund_amount"] == 10.0

