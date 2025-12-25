"""
Enrollment Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestEnrollment:
    """Test lesson enrollment"""
    
    def test_enroll_in_lesson_as_student(self, client):
        """
        Test that student can enroll in a lesson
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # Register student
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
        
        # Create lesson as admin
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
            json={
                "level": "N5",
                "title": "Test Lesson",
                "description": "Test",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Enroll in lesson
        response = client.post(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "enrollment_id" in data
        assert data["lesson_id"] == lesson_id
        assert data["status"] == "active"
    
    def test_enroll_requires_auth(self, client):
        """
        Test that enrollment requires authentication
        
        RED - This test SHOULD FAIL
        """
        response = client.post("/api/enrollments/any-lesson-id")
        
        assert response.status_code == 403  # Forbidden
    
    def test_cannot_enroll_twice_in_same_lesson(self, client):
        """
        Test that user cannot enroll twice in the same lesson
        
        RED - This test SHOULD FAIL
        """
        # Setup
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
        
        # Enroll first time
        client.post(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Try to enroll again
        response = client.post(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 400  # Bad request - already enrolled


class TestEnrollmentRetrieval:
    """Test enrollment retrieval"""
    
    def test_get_my_enrollments(self, client):
        """
        Test getting user's enrolled lessons
        
        RED - This test SHOULD FAIL
        """
        # Register and enroll
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
        
        # Create and enroll in two lessons
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
        
        client.post(
            f"/api/enrollments/{lesson1}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        client.post(
            f"/api/enrollments/{lesson2}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Get my enrollments
        response = client.get(
            "/api/enrollments/my-enrollments",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_check_enrollment_status(self, client):
        """
        Test checking if enrolled in specific lesson
        
        RED - This test SHOULD FAIL
        """
        # Setup
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
        
        # Enroll
        client.post(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Check enrollment status
        response = client.get(
            f"/api/enrollments/status/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enrolled"] == True
        assert data["lesson_id"] == lesson_id


class TestUnenrollment:
    """Test unenrollment"""
    
    def test_unenroll_from_lesson(self, client):
        """
        Test that user can unenroll from a lesson
        
        RED - This test SHOULD FAIL
        """
        # Setup and enroll
        client.post("/api/auth/register", json={
            "email": "student5@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student5@example.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "admin5@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin5@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Enroll
        client.post(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Unenroll
        response = client.delete(
            f"/api/enrollments/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify unenrolled
        status_response = client.get(
            f"/api/enrollments/status/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert status_response.json()["enrolled"] == False
