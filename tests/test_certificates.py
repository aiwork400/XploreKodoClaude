"""
Certificate Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestCertificateGeneration:
    """Test certificate generation"""
    
    def test_generate_certificate_after_lesson_completion(self, client):
        """
        Test that student can generate certificate after completing lesson
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # Setup student and lesson
        client.post("/api/auth/register", json={
            "email": "student@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student@example.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Basic Japanese", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Mark lesson as 100% complete
        client.post(
            "/api/progress",
            json={"lesson_id": lesson_id, "completed_percentage": 100, "notes": "Completed!"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Generate certificate
        response = client.post(
            f"/api/certificates/generate/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "certificate_id" in data
        assert data["lesson_id"] == lesson_id
        assert "issued_at" in data
    
    def test_cannot_generate_certificate_without_completion(self, client):
        """
        Test that certificate requires 100% completion
        
        RED - This test SHOULD FAIL
        """
        client.post("/api/auth/register", json={
            "email": "student2@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student2@example.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "admin2@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin2@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Only 50% complete
        client.post(
            "/api/progress",
            json={"lesson_id": lesson_id, "completed_percentage": 50},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Try to generate certificate
        response = client.post(
            f"/api/certificates/generate/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 400  # Bad request - not completed


class TestCertificateRetrieval:
    """Test certificate retrieval"""
    
    def test_get_my_certificates(self, client):
        """
        Test getting user's certificates
        
        RED - This test SHOULD FAIL
        """
        # Setup and generate certificate
        client.post("/api/auth/register", json={
            "email": "student3@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student3@example.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "admin3@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin3@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        # Create two lessons and complete them
        lesson1 = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Lesson 1", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["lesson_id"]
        
        lesson2 = client.post(
            "/api/lessons",
            json={"level": "N4", "title": "Lesson 2", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["lesson_id"]
        
        # Complete both
        client.post(
            "/api/progress",
            json={"lesson_id": lesson1, "completed_percentage": 100},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        client.post(
            "/api/progress",
            json={"lesson_id": lesson2, "completed_percentage": 100},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Generate certificates
        client.post(
            f"/api/certificates/generate/{lesson1}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        client.post(
            f"/api/certificates/generate/{lesson2}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Get certificates
        response = client.get(
            "/api/certificates/my-certificates",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_cannot_duplicate_certificate(self, client):
        """
        Test that user cannot generate duplicate certificate
        
        RED - This test SHOULD FAIL
        """
        client.post("/api/auth/register", json={
            "email": "student4@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student4@example.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "admin4@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin4@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Complete lesson
        client.post(
            "/api/progress",
            json={"lesson_id": lesson_id, "completed_percentage": 100},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Generate certificate first time
        client.post(
            f"/api/certificates/generate/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Try to generate again
        response = client.post(
            f"/api/certificates/generate/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 400  # Already has certificate
