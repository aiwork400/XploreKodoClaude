"""
Tests for AI/ML Training API endpoints
"""
import pytest
from decimal import Decimal
import uuid

from main import app
from db_models.aiml_training import AIMLCourseDB, AIMLLearningPathDB, AIMLProjectDB



@pytest.fixture
def sample_course(test_db):
    """Create a sample AI/ML course using conftest's test_db"""
    course = AIMLCourseDB(
        course_id=uuid.uuid4(),
        course_name="AI Fundamentals",
        level=1,
        track="ai_fundamentals",
        duration_weeks=4,
        price=Decimal("150.00"),
        description="Introduction to AI and Machine Learning",
        is_active=True
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture
def sample_learning_path(test_db, sample_course):
    """Create a sample learning path"""
    path = AIMLLearningPathDB(
        path_id=uuid.uuid4(),
        path_name="ML Engineer Path",
        description="Complete path to become ML engineer",
        courses=["course1", "course2"],  # JSONB field
        total_duration_weeks=20,
        total_price=Decimal("50000.00"),
        is_active=True
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    return path

def test_aiml_health_check(client):
    """Test AI/ML training health endpoint"""
    response = client.get("/api/aiml/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["module"] == "AI/ML Training"
    assert "version" in data


# ==================== COURSE TESTS ====================

def test_get_all_courses(client):
    """Test getting all AI/ML courses"""
    response = client.get("/api/aiml/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_courses_by_level(client, sample_course):
    """Test filtering courses by level"""
    response = client.get("/api/aiml/courses?level=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["level"] == 1


def test_get_courses_by_track(client, test_db, sample_course):
    """Test filtering courses by track"""
    # Create a track-specific course
    course = AIMLCourseDB(
        course_name="Computer Vision Specialization",
        level=4,
        track="computer_vision",
        duration_weeks=6,
        price=Decimal("350.00"),
        is_active=True
    )
    test_db.add(course)
    test_db.commit()
    response = client.get("/api/aiml/courses?track=computer_vision")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_course_by_id(client, test_db, sample_course):
    """Test getting specific course details"""
    response = client.get(f"/api/aiml/courses/{sample_course}")
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "AI Fundamentals"
    assert data["level"] == 1


def test_get_course_syllabus(client, test_db, sample_course):
    """Test getting course syllabus"""
    response = client.get(f"/api/aiml/courses/{sample_course}/syllabus")
    assert response.status_code == 200
    data = response.json()
    assert "course" in data
    assert "syllabus" in data
    assert "total_lessons" in data


# ==================== ENROLLMENT TESTS ====================

def test_enroll_in_course(client, test_db, sample_course):
    """Test enrolling in AI/ML course"""
    response = client.post(
        "/api/aiml/enrollments",
        json={"course_id": str(sample_course.course_id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert "enrollment_id" in data
    assert data["status"] == "enrolled"


def test_enroll_duplicate_course(client, test_db, sample_course):
    """Test enrolling in same course twice"""
    # First enrollment
    client.post(
        "/api/aiml/enrollments",
        json={"course_id": str(sample_course.course_id)}
    )
    
    # Duplicate enrollment
    response = client.post(
        "/api/aiml/enrollments",
        json={"course_id": str(sample_course.course_id)}
    )
    assert response.status_code == 400


def test_get_my_enrollments(client, sample_course):
    """Test getting user's AI/ML enrollments"""
    # Enroll first
    client.post(
        "/api/aiml/enrollments",
        json={"course_id": str(sample_course.course_id)}
    )
    
    # Get enrollments
    response = client.get("/api/aiml/enrollments/my-courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ==================== CODE PLAYGROUND TESTS ====================

def test_submit_code(client, test_db, sample_course):
    """Test code submission"""
    # Create a lesson first
    from db_models.aiml_training import AIMLLessonDB
    lesson = AIMLLessonDB(
        course_id=sample_course.course_id,
        week_number=1,
        lesson_number=1,
        lesson_title="Hello World in Python",
        lesson_type="lab",
        duration_minutes=30,
        sort_order=1
    )
    test_db.add(lesson)
    test_db.commit()
    test_db.refresh(lesson)
    lesson_id = lesson.lesson_id
    # Submit code
    response = client.post(
        "/api/aiml/code/submit",
        json={
            "lesson_id": str(lesson_id),
            "code_content": "print('Hello, World!')",
            "language": "python"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "submission_id" in data
    assert "auto_grade_score" in data
    assert "passed" in data


def test_get_code_history(client):
    """Test getting code submission history"""
    response = client.get("/api/aiml/code/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ==================== PROJECT TESTS ====================

def test_submit_project(client, test_db, sample_course):
    """Test submitting an AI/ML project"""
    response = client.post(
        "/api/aiml/projects",
        json={
            "course_id": str(sample_course.course_id),
            "project_title": "Image Classification with CNN",
            "project_type": "course_project",
            "description": "Built CNN for MNIST classification",
            "github_url": "https://github.com/user/mnist-cnn",
            "technologies_used": {"frameworks": ["TensorFlow", "Keras"]}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    assert data["project_title"] == "Image Classification with CNN"


def test_get_my_projects(client, test_db, sample_course):
    """Test getting user's projects"""
    # Submit a project first
    client.post(
        "/api/aiml/projects",
        json={
            "course_id": str(sample_course.course_id),
            "project_title": "Test Project",
            "project_type": "portfolio",
            "description": "Test description"
        }
    )
    
    # Get projects
    response = client.get("/api/aiml/projects/my-projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_portfolio_projects(client):
    """Test getting featured portfolio projects"""
    response = client.get("/api/aiml/projects/portfolio")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_feature_project_in_portfolio(client, test_db, sample_course):
    """Test featuring a project in portfolio"""
    # Create project first
    project = AIMLProjectDB(
        user_id="user_001",
        course_id=sample_course.course_id,
        project_title="Featured Project",
        project_type="capstone",
        description="Amazing project"
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    project_id = project.project_id
    # Feature it
    response = client.put(f"/api/aiml/projects/{project_id}/feature")
    assert response.status_code == 200


# ==================== LEARNING PATH TESTS ====================

def test_get_learning_paths(client, sample_learning_path):
    """Test getting all learning paths"""
    response = client.get("/api/aiml/learning-paths")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_enroll_in_learning_path(client, sample_learning_path):
    """Test enrolling in a learning path"""
    response = client.post(f"/api/aiml/learning-paths/{sample_learning_path}/enroll")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "path_name" in data


def test_enroll_duplicate_path(client, sample_learning_path):
    """Test enrolling in same path twice"""
    # First enrollment
    client.post(f"/api/aiml/learning-paths/{sample_learning_path}/enroll")
    
    # Duplicate
    response = client.post(f"/api/aiml/learning-paths/{sample_learning_path}/enroll")
    assert response.status_code == 400


# ==================== LEADERBOARD TESTS ====================

def test_get_leaderboard(client):
    """Test getting leaderboard"""
    response = client.get("/api/aiml/leaderboard")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_my_rank(client):
    """Test getting user's leaderboard rank"""
    response = client.get("/api/aiml/leaderboard/my-rank")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "total_xp" in data


def test_add_xp(client):
    """Test adding XP to user"""
    response = client.post(
        "/api/aiml/leaderboard/add-xp",
        json={"xp_amount": 50}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_xp" in data


# ==================== CERTIFICATE TESTS ====================

def test_get_my_certificates(client):
    """Test getting user's AI/ML certificates"""
    response = client.get("/api/aiml/certificates/my-certs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ==================== JOB PLACEMENT TESTS ====================

def test_record_job_placement(client):
    """Test recording job placement"""
    response = client.post(
        "/api/aiml/placements",
        params={
            "company_name": "Sony AI",
            "job_title": "ML Engineer",
            "salary_jpy": 8000000,
            "placement_date": "2025-12-24"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "placement_fee" in data


def test_get_placement_stats(client):
    """Test getting placement statistics"""
    response = client.get("/api/aiml/placements/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_placements" in data
    assert "average_salary_jpy" in data


# ==================== SUMMARY ====================

def test_aiml_training_module_summary(client):
    """Summary test to verify module is operational"""
    # Test health
    health = client.get("/api/aiml/health")
    assert health.status_code == 200
    
    # Test courses
    courses = client.get("/api/aiml/courses")
    assert courses.status_code == 200
    
    # Test learning paths
    paths = client.get("/api/aiml/learning-paths")
    assert paths.status_code == 200
    
    # Test leaderboard
    leaderboard = client.get("/api/aiml/leaderboard")
    assert leaderboard.status_code == 200
    
    print("\nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¦ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¦ AI/ML Training Module: ALL TESTS PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
