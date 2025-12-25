"""
Quiz Tests - TDD
Tests MUST be written BEFORE implementation code
"""
from fastapi.testclient import TestClient
import pytest


class TestQuizCreation:
    """Test quiz creation (admin only)"""
    
    def test_create_quiz_as_admin(self, client):
        """
        Test that admin can create a quiz for a lesson
        
        RED - This test SHOULD FAIL (endpoint doesn't exist yet)
        """
        # Setup admin and lesson
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
            json={"level": "N5", "title": "Test Lesson", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Create quiz
        response = client.post(
            "/api/quizzes",
            json={
                "lesson_id": lesson_id,
                "title": "N5 Vocabulary Quiz",
                "questions": [
                    {
                        "question_text": "What does 'こんにちは' mean?",
                        "options": ["Hello", "Goodbye", "Thank you", "Sorry"],
                        "correct_answer": "A"
                    },
                    {
                        "question_text": "What does 'ありがとう' mean?",
                        "options": ["Hello", "Goodbye", "Thank you", "Sorry"],
                        "correct_answer": "C"
                    }
                ]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "quiz_id" in data
        assert data["title"] == "N5 Vocabulary Quiz"
        assert len(data["questions"]) == 2
    
    def test_create_quiz_requires_admin(self, client):
        """
        Test that only admin can create quizzes
        
        RED - This test SHOULD FAIL
        """
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
        
        response = client.post(
            "/api/quizzes",
            json={
                "lesson_id": "any-lesson",
                "title": "Test",
                "questions": []
            },
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403


class TestQuizRetrieval:
    """Test quiz retrieval"""
    
    def test_get_quizzes_for_lesson(self, client):
        """
        Test getting all quizzes for a lesson
        
        RED - This test SHOULD FAIL
        """
        # Setup
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
        
        # Create quiz
        client.post(
            "/api/quizzes",
            json={
                "lesson_id": lesson_id,
                "title": "Quiz 1",
                "questions": [{"question_text": "Test?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Get quizzes
        response = client.get(f"/api/quizzes/lesson/{lesson_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


class TestQuizSubmission:
    """Test quiz submission and grading"""
    
    def test_submit_quiz_answers(self, client):
        """
        Test that student can submit quiz answers and get graded
        
        RED - This test SHOULD FAIL
        """
        # Setup admin and create quiz
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
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        quiz_response = client.post(
            "/api/quizzes",
            json={
                "lesson_id": lesson_id,
                "title": "Test Quiz",
                "questions": [
                    {"question_text": "Q1", "options": ["A", "B", "C", "D"], "correct_answer": "A"},
                    {"question_text": "Q2", "options": ["A", "B", "C", "D"], "correct_answer": "B"}
                ]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        quiz_id = quiz_response.json()["quiz_id"]
        
        # Setup student
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
        
        # Submit answers
        response = client.post(
            f"/api/quizzes/{quiz_id}/submit",
            json={
                "answers": ["A", "B"]  # Both correct
            },
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "attempt_id" in data
        assert data["score"] == 100  # 2/2 correct = 100%
        assert data["total_questions"] == 2
        assert data["correct_answers"] == 2
    
    def test_submit_quiz_partial_correct(self, client):
        """
        Test quiz submission with partial correct answers
        
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
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        quiz_response = client.post(
            "/api/quizzes",
            json={
                "lesson_id": lesson_id,
                "title": "Test",
                "questions": [
                    {"question_text": "Q1", "options": ["A", "B", "C", "D"], "correct_answer": "A"},
                    {"question_text": "Q2", "options": ["A", "B", "C", "D"], "correct_answer": "B"}
                ]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        quiz_id = quiz_response.json()["quiz_id"]
        
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
        
        # Submit with one wrong answer
        response = client.post(
            f"/api/quizzes/{quiz_id}/submit",
            json={"answers": ["A", "C"]},  # Second answer wrong
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == 50  # 1/2 correct = 50%
        assert data["correct_answers"] == 1


class TestQuizAttempts:
    """Test quiz attempt history"""
    
    def test_get_my_quiz_attempts(self, client):
        """
        Test getting user's quiz attempt history
        
        RED - This test SHOULD FAIL
        """
        # Setup and submit quiz
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
        
        quiz_response = client.post(
            "/api/quizzes",
            json={
                "lesson_id": lesson_id,
                "title": "Test",
                "questions": [{"question_text": "Q", "options": ["A", "B", "C", "D"], "correct_answer": "A"}]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        quiz_id = quiz_response.json()["quiz_id"]
        
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
        
        # Submit quiz twice
        client.post(
            f"/api/quizzes/{quiz_id}/submit",
            json={"answers": ["A"]},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        client.post(
            f"/api/quizzes/{quiz_id}/submit",
            json={"answers": ["B"]},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        # Get attempts
        response = client.get(
            "/api/quizzes/my-attempts",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
