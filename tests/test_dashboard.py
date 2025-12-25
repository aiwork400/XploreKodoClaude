"""
Dashboard Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestUserDashboard:
    """Test user dashboard statistics"""
    
    def test_get_user_dashboard_stats(self, client):
        """Test getting comprehensive user dashboard statistics"""
        client.post("/api/auth/register", json={"email": "student@example.com", "password": "StudentPass123!", "role": "student"})
        student_login = client.post("/api/auth/login", json={"email": "student@example.com", "password": "StudentPass123!"})
        student_token = student_login.json()["access_token"]
        
        client.post("/api/auth/register", json={"email": "admin@example.com", "password": "AdminPass123!", "role": "admin"})
        admin_login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "AdminPass123!"})
        admin_token = admin_login.json()["access_token"]
        
        lesson1 = client.post("/api/lessons", json={"level": "N5", "title": "Lesson 1", "description": "Test", "content_json": {}}, headers={"Authorization": f"Bearer {admin_token}"}).json()["lesson_id"]
        lesson2_id = client.post("/api/lessons", json={"level": "N4", "title": "Lesson 2", "description": "Test", "content_json": {}}, headers={"Authorization": f"Bearer {admin_token}"}).json()["lesson_id"]
        
        quiz_id = client.post("/api/quizzes", json={"lesson_id": lesson1, "title": "Test Quiz", "questions": [{"question_text": "Q1", "options": ["A", "B", "C", "D"], "correct_answer": "A"}]}, headers={"Authorization": f"Bearer {admin_token}"}).json()["quiz_id"]
        
        client.post("/api/progress", json={"lesson_id": lesson1, "completed_percentage": 100}, headers={"Authorization": f"Bearer {student_token}"})
        client.post(f"/api/certificates/generate/{lesson1}", headers={"Authorization": f"Bearer {student_token}"})
        client.post("/api/progress", json={"lesson_id": lesson2_id, "completed_percentage": 50}, headers={"Authorization": f"Bearer {student_token}"})
        client.post(f"/api/quizzes/{quiz_id}/submit", json={"answers": ["A"]}, headers={"Authorization": f"Bearer {student_token}"})
        
        response = client.get("/api/dashboard/my-stats", headers={"Authorization": f"Bearer {student_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["lessons_completed"] == 1
        assert data["certificates_earned"] == 1
        assert data["quizzes_taken"] == 1
        assert data["average_quiz_score"] == 100
    
    def test_dashboard_requires_auth(self, client):
        """Test that dashboard requires authentication"""
        response = client.get("/api/dashboard/my-stats")
        assert response.status_code == 403
    
    def test_dashboard_with_no_activity(self, client):
        """Test dashboard for user with no activity"""
        client.post("/api/auth/register", json={"email": "newstudent@example.com", "password": "StudentPass123!", "role": "student"})
        login = client.post("/api/auth/login", json={"email": "newstudent@example.com", "password": "StudentPass123!"})
        token = login.json()["access_token"]
        
        response = client.get("/api/dashboard/my-stats", headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_lessons_enrolled"] == 0
        assert data["lessons_completed"] == 0
        assert data["certificates_earned"] == 0
        assert data["quizzes_taken"] == 0
        assert data["average_quiz_score"] == 0
