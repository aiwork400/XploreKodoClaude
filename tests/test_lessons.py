"""
Lesson Management Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestLessonCreation:
    """Test lesson creation (admin only)"""
    
    def test_create_lesson_as_admin_success(self, client):
        """
        Test that admin can create lesson
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # First, register and login as admin
        client.post("/api/auth/register", json={
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "AdminPass123!"
        })
        token = login_response.json()["access_token"]
        
        # Now create a lesson
        response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Basic Greetings",
                "description": "Learn basic Japanese greetings",
                "content_json": {
                    "phrases": ["?????", "????"]
                }
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "lesson_id" in data
        assert data["title"] == "Basic Greetings"
        assert data["level"] == "N5"
    
    def test_create_lesson_as_student_fails(self, client):
        """
        Test that student cannot create lesson
        
        RED - This test SHOULD FAIL
        """
        # Register as student
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
        
        # Try to create lesson (should fail)
        response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Test Lesson",
                "description": "Test",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403  # Forbidden
    
    def test_create_lesson_without_auth_fails(self, client):
        """
        Test that unauthenticated user cannot create lesson
        
        RED - This test SHOULD FAIL
        """
        response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Test",
                "description": "Test",
                "content_json": {}
            }
        )
        
        assert response.status_code == 403  # Forbidden (no token provided)


class TestLessonRetrieval:
    """Test lesson retrieval (all users)"""
    
    def test_list_all_lessons(self, client):
        """
        Test listing all lessons
        
        RED - This test SHOULD FAIL
        """
        response = client.get("/api/lessons")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_specific_lesson(self, client):
        """
        Test getting a specific lesson
        
        RED - This test SHOULD FAIL
        """
        # First create a lesson as admin
        client.post("/api/auth/register", json={
            "email": "admin2@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "admin2@example.com",
            "password": "AdminPass123!"
        })
        token = login_response.json()["access_token"]
        
        create_response = client.post(
            "/api/lessons",
            json={
                "level": "N4",
                "title": "Numbers",
                "description": "Learn numbers",
                "content_json": {"numbers": [1, 2, 3]}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        lesson_id = create_response.json()["lesson_id"]
        
        # Now get that lesson
        response = client.get(f"/api/lessons/{lesson_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["lesson_id"] == lesson_id
        assert data["title"] == "Numbers"
    
    def test_get_nonexistent_lesson_fails(self, client):
        """
        Test that getting non-existent lesson returns 404
        
        RED - This test SHOULD FAIL
        """
        response = client.get("/api/lessons/nonexistent-id")
        
        assert response.status_code == 404


class TestLessonUpdate:
    """Test lesson updates (admin only)"""
    
    def test_update_lesson_as_admin_success(self, client):
        """
        Test that admin can update lesson
        
        RED - This test SHOULD FAIL
        """
        # Create lesson
        client.post("/api/auth/register", json={
            "email": "admin3@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "admin3@example.com",
            "password": "AdminPass123!"
        })
        token = login_response.json()["access_token"]
        
        create_response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Original Title",
                "description": "Original",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        lesson_id = create_response.json()["lesson_id"]
        
        # Update lesson
        response = client.put(
            f"/api/lessons/{lesson_id}",
            json={
                "level": "N4",
                "title": "Updated Title",
                "description": "Updated",
                "content_json": {"new": "data"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["level"] == "N4"
    
    def test_update_lesson_as_student_fails(self, client):
        """
        Test that student cannot update lesson
        
        RED - This test SHOULD FAIL
        """
        # Create lesson as admin
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
        
        create_response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Test",
                "description": "Test",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = create_response.json()["lesson_id"]
        
        # Try to update as student
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
        
        response = client.put(
            f"/api/lessons/{lesson_id}",
            json={"title": "Hacked"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403


class TestLessonDeletion:
    """Test lesson deletion (admin only)"""
    
    def test_delete_lesson_as_admin_success(self, client):
        """
        Test that admin can delete lesson
        
        RED - This test SHOULD FAIL
        """
        # Create lesson
        client.post("/api/auth/register", json={
            "email": "admin5@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        login_response = client.post("/api/auth/login", json={
            "email": "admin5@example.com",
            "password": "AdminPass123!"
        })
        token = login_response.json()["access_token"]
        
        create_response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "To Delete",
                "description": "Test",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        lesson_id = create_response.json()["lesson_id"]
        
        # Delete lesson
        response = client.delete(
            f"/api/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/lessons/{lesson_id}")
        assert get_response.status_code == 404
    
    def test_delete_lesson_as_student_fails(self, client):
        """
        Test that student cannot delete lesson
        
        RED - This test SHOULD FAIL
        """
        # Create lesson as admin
        client.post("/api/auth/register", json={
            "email": "admin6@example.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin6@example.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        create_response = client.post(
            "/api/lessons",
            json={
                "level": "N5",
                "title": "Test",
                "description": "Test",
                "content_json": {}
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = create_response.json()["lesson_id"]
        
        # Try to delete as student
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
        
        response = client.delete(
            f"/api/lessons/{lesson_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403
