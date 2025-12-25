"""
Payment Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestPaymentIntentCreation:
    """Test payment intent creation"""
    
    def test_create_payment_intent_as_student(self, client):
        """
        Test that student can create a payment intent
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # Register and login as student
        client.post("/api/auth/register", json={
            "email": "student@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": "StudentPass123!"
        })
        token = login_response.json()["access_token"]
        
        # Create payment intent
        response = client.post(
            "/api/payments/create-intent",
            json={
                "amount": 1999,  # $19.99
                "currency": "usd",
                "description": "N5 Course Purchase"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "client_secret" in data
        assert "payment_intent_id" in data
        assert data["amount"] == 1999
    
    def test_create_payment_intent_requires_auth(self, client):
        """
        Test that payment intent creation requires authentication
        
        RED - This test SHOULD FAIL
        """
        response = client.post(
            "/api/payments/create-intent",
            json={
                "amount": 1999,
                "currency": "usd",
                "description": "Test"
            }
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_create_payment_intent_validates_amount(self, client):
        """
        Test that amount must be positive
        
        RED - This test SHOULD FAIL
        """
        client.post("/api/auth/register", json={
            "email": "student2@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "student2@example.com",
            "password": "StudentPass123!"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/payments/create-intent",
            json={
                "amount": -100,
                "currency": "usd",
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400  # Validation error


class TestPaymentHistory:
    """Test payment history retrieval"""
    
    def test_get_my_payment_history(self, client):
        """
        Test getting user's own payment history
        
        RED - This test SHOULD FAIL
        """
        # Register and login
        client.post("/api/auth/register", json={
            "email": "student3@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "student3@example.com",
            "password": "StudentPass123!"
        })
        token = login_response.json()["access_token"]
        
        # Get payment history
        response = client.get(
            "/api/payments/my-payments",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_payment_history_requires_auth(self, client):
        """
        Test that payment history requires authentication
        
        RED - This test SHOULD FAIL
        """
        response = client.get("/api/payments/my-payments")
        
        assert response.status_code == 403


class TestPaymentStatusTracking:
    """Test payment status tracking"""
    
    def test_get_payment_status(self, client):
        """
        Test getting payment status by ID
        
        RED - This test SHOULD FAIL
        """
        # Setup
        client.post("/api/auth/register", json={
            "email": "student4@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "student4@example.com",
            "password": "StudentPass123!"
        })
        token = login_response.json()["access_token"]
        
        # Create payment intent
        create_response = client.post(
            "/api/payments/create-intent",
            json={
                "amount": 2999,
                "currency": "usd",
                "description": "Test"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        payment_intent_id = create_response.json()["payment_intent_id"]
        
        # Get payment status
        response = client.get(
            f"/api/payments/status/{payment_intent_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "amount" in data
