"""
Progress Tracking Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestProgressCreationAndUpdate:
    """Test progress creation and updates"""
    
    def test_create_progress_as_student(self, client):
        """
        Test that student can create/update their own progress
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # Register student and create lesson
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
        
        # Create progress
        response = client.post(
            "/api/progress",
            json={
                "lesson_id": lesson_id,
                "completed_percentage": 50,
                "notes": "Halfway through"
            },
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "progress_id" in data
        assert data["lesson_id"] == lesson_id
        assert data["completed_percentage"] == 50
    
    def test_update_existing_progress(self, client):
        """
        Test updating existing progress
        
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
        
        # Create initial progress
        client.post(
            "/api/progress",
            json={"lesson_id": lesson_id, "completed_percentage": 30},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Update progress
        response = client.post(
            "/api/progress",
            json={"lesson_id": lesson_id, "completed_percentage": 80, "notes": "Almost done!"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["completed_percentage"] == 80
        assert data["notes"] == "Almost done!"
    
    def test_progress_percentage_validation(self, client):
        """
        Test that percentage must be 0-100
        
        RED - This test SHOULD FAIL
        """
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
        
        response = client.post(
            "/api/progress",
            json={"lesson_id": "any-id", "completed_percentage": 150},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 400  # Validation error


class TestProgressRetrieval:
    """Test progress retrieval"""
    
    def test_get_user_progress(self, client):
        """
        Test getting user's own progress
        
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
        user_id = student_login.json().get("user_id") or "test-user-id"
        
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
        
        # Create lessons and progress
        lesson1 = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Lesson 1", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["lesson_id"]
        
        lesson2 = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Lesson 2", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        ).json()["lesson_id"]
        
        client.post(
            "/api/progress",
            json={"lesson_id": lesson1, "completed_percentage": 100},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        client.post(
            "/api/progress",
            json={"lesson_id": lesson2, "completed_percentage": 50},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Get user's progress
        response = client.get(
            "/api/progress/my-progress",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_get_lesson_progress_stats(self, client):
        """
        Test getting progress stats for a lesson (admin only)
        
        RED - This test SHOULD FAIL
        """
        # Setup
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
            json={"level": "N5", "title": "Stats Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Get lesson stats
        response = client.get(
            f"/api/progress/lesson/{lesson_id}/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "lesson_id" in data
        assert "total_students" in data
        assert "average_completion" in data
    
    def test_student_cannot_see_other_student_progress(self, client):
        """
        Test that students can only see their own progress
        
        RED - This test SHOULD FAIL
        """
        # Create two students
        client.post("/api/auth/register", json={
            "email": "student5@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student1_login = client.post("/api/auth/login", json={
            "email": "student5@example.com",
            "password": "StudentPass123!"
        })
        student1_token = student1_login.json()["access_token"]
        
        client.post("/api/auth/register", json={
            "email": "student6@example.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student2_login = client.post("/api/auth/login", json={
            "email": "student6@example.com",
            "password": "StudentPass123!"
        })
        student2_token = student2_login.json()["access_token"]
        
        # Student 1 gets their progress
        response = client.get(
            "/api/progress/my-progress",
            headers={"Authorization": f"Bearer {student1_token}"}
        )
        
        # Should only see their own progress
        assert response.status_code == 200
        data = response.json()
        # All progress should belong to student1
        for item in data:
            assert item["user_id"] != "student6@example.com"
