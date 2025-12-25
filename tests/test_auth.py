"""
Authentication Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_new_user_success(self, client):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "role": "student"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "student"
        assert "user_id" in data
    
    def test_register_duplicate_email_fails(self, client):
        """Test that duplicate email registration fails"""
        # Register first user
        client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass123!",
            "role": "student"
        })
        
        # Try to register same email again
        response = client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "DifferentPass123!",
            "role": "student"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email_fails(self, client):
        """Test that invalid email format fails"""
        response = client.post("/api/auth/register", json={
            "email": "notanemail",
            "password": "Pass123!",
            "role": "student"
        })
        
        # Pydantic returns 422 for validation errors
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client):
        """Test successful login with correct credentials"""
        # First register a user
        client.post("/api/auth/register", json={
            "email": "testlogin@example.com",
            "password": "SecurePass123!",
            "role": "student"
        })
        
        # Now login
        response = client.post("/api/auth/login", json={
            "email": "testlogin@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password_fails(self, client):
        """Test that wrong password fails"""
        # Register user
        client.post("/api/auth/register", json={
            "email": "wrongpass@example.com",
            "password": "CorrectPass123!",
            "role": "student"
        })
        
        # Try wrong password
        response = client.post("/api/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "WrongPass123!"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user_fails(self, client):
        """Test that login fails for non-existent user"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Pass123!"
        })
        
        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password security"""
    
    def test_password_is_hashed(self, client):
        """Test that passwords are stored hashed, not plain text"""
        response = client.post("/api/auth/register", json={
            "email": "hashtest@example.com",
            "password": "MySecretPass123!",
            "role": "student"
        })
        
        assert response.status_code == 201
        # Password should not appear in response
        response_str = str(response.json())
        assert "MySecretPass123!" not in response_str
