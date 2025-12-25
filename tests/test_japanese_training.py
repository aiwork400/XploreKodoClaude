"""
Tests for Japanese Language Training Module
Tests courses, vocabulary, kanji, enrollments, quizzes, and progress tracking
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from decimal import Decimal

from main import app
from config.database import Base, get_db
from db_models.japanese_training import (
    JapaneseCourseDB,
    JapaneseVocabularyDB,
    JapaneseKanjiDB,
    JapaneseEnrollmentDB,
    JapaneseQuizDB
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_japanese.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_course(setup_database):
    """Create a sample Japanese course"""
    db = TestingSessionLocal()
    course = JapaneseCourseDB(
        level="N5",
        course_name="Japanese N5 Beginner",
        jlpt_level_num=5,
        duration_weeks=12,
        price_self_paced=Decimal("100.00"),
        price_interactive=Decimal("150.00"),
        vocabulary_count=800,
        kanji_count=100,
        grammar_patterns=30,
        is_active=True
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    course_id = course.course_id
    db.close()
    yield course_id


@pytest.fixture
def sample_vocabulary(setup_database):
    """Create sample vocabulary words"""
    db = TestingSessionLocal()
    vocab = JapaneseVocabularyDB(
        word_hiragana="こんにちは",
        word_kanji="今日は",
        word_romaji="konnichiwa",
        english_meaning="Hello, Good afternoon",
        part_of_speech="greeting",
        jlpt_level="N5",
        frequency_rank=1
    )
    db.add(vocab)
    db.commit()
    db.refresh(vocab)
    vocab_id = vocab.vocab_id
    db.close()
    yield vocab_id


# ==================== HEALTH CHECK TESTS ====================

def test_japanese_health_check(client):
    """Test Japanese training health endpoint"""
    response = client.get("/api/japanese/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["module"] == "Japanese Language Training"
    assert "version" in data


# ==================== COURSE TESTS ====================

def test_get_all_courses(client):
    """Test getting all Japanese courses"""
    response = client.get("/api/japanese/courses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_courses_by_level(client, sample_course):
    """Test filtering courses by level"""
    response = client.get("/api/japanese/courses?level=N5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["level"] == "N5"


def test_get_course_by_id(client, sample_course):
    """Test getting specific course details"""
    response = client.get(f"/api/japanese/courses/{sample_course}")
    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "N5"
    assert data["course_name"] == "Japanese N5 Beginner"
    assert data["duration_weeks"] == 12


def test_get_course_syllabus(client, sample_course):
    """Test getting course syllabus"""
    response = client.get(f"/api/japanese/courses/{sample_course}/syllabus")
    assert response.status_code == 200
    data = response.json()
    assert "course" in data
    assert "syllabus" in data
    assert "total_lessons" in data


def test_get_nonexistent_course(client):
    """Test getting course that doesn't exist"""
    fake_id = uuid.uuid4()
    response = client.get(f"/api/japanese/courses/{fake_id}")
    assert response.status_code == 404


# ==================== ENROLLMENT TESTS ====================

def test_enroll_in_course(client, sample_course):
    """Test enrolling in a Japanese course"""
    response = client.post(
        "/api/japanese/enrollments",
        json={
            "course_id": str(sample_course),
            "delivery_mode": "self_paced"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "enrollment_id" in data
    assert data["status"] == "enrolled"
    assert data["progress_percentage"] == "0.00"


def test_enroll_duplicate_course(client, sample_course):
    """Test enrolling in same course twice (should fail)"""
    # First enrollment
    client.post(
        "/api/japanese/enrollments",
        json={
            "course_id": str(sample_course),
            "delivery_mode": "interactive"
        }
    )
    
    # Second enrollment (duplicate)
    response = client.post(
        "/api/japanese/enrollments",
        json={
            "course_id": str(sample_course),
            "delivery_mode": "premium"
        }
    )
    assert response.status_code == 400


def test_get_my_enrollments(client, sample_course):
    """Test getting user's enrollments"""
    # Enroll first
    client.post(
        "/api/japanese/enrollments",
        json={
            "course_id": str(sample_course),
            "delivery_mode": "self_paced"
        }
    )
    
    # Get enrollments
    response = client.get("/api/japanese/enrollments/my-courses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ==================== VOCABULARY TESTS ====================

def test_get_vocabulary_by_level(client, sample_vocabulary):
    """Test getting vocabulary by JLPT level"""
    response = client.get("/api/japanese/vocabulary/level/N5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_vocabulary_details(client, sample_vocabulary):
    """Test getting specific vocabulary word"""
    response = client.get(f"/api/japanese/vocabulary/{sample_vocabulary}")
    assert response.status_code == 200
    data = response.json()
    assert data["word_hiragana"] == "こんにちは"
    assert data["english_meaning"] == "Hello, Good afternoon"


def test_search_vocabulary(client, sample_vocabulary):
    """Test vocabulary search"""
    response = client.get("/api/japanese/vocabulary/search?query=hello")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_review_vocabulary_correct(client, sample_vocabulary):
    """Test SRS vocabulary review (correct answer)"""
    response = client.post(
        f"/api/japanese/vocabulary/{sample_vocabulary}/review",
        json={"correct": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] == True
    assert "srs_level" in data
    assert "next_review_date" in data


def test_review_vocabulary_incorrect(client, sample_vocabulary):
    """Test SRS vocabulary review (incorrect answer)"""
    response = client.post(
        f"/api/japanese/vocabulary/{sample_vocabulary}/review",
        json={"correct": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["correct"] == False
    assert "srs_level" in data


# ==================== KANJI TESTS ====================

def test_get_kanji_by_level(client):
    """Test getting kanji by level"""
    response = client.get("/api/japanese/kanji/level/N5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_practice_kanji(client):
    """Test kanji practice recording"""
    # First create a kanji
    db = TestingSessionLocal()
    kanji = JapaneseKanjiDB(
        character="日",
        kunyomi="ひ、か",
        onyomi="ニチ、ジツ",
        english_meaning="day, sun",
        stroke_count=4,
        jlpt_level="N5",
        frequency_rank=1
    )
    db.add(kanji)
    db.commit()
    db.refresh(kanji)
    kanji_id = kanji.kanji_id
    db.close()
    
    # Practice
    response = client.post(f"/api/japanese/kanji/{kanji_id}/practice")
    assert response.status_code == 200
    data = response.json()
    assert "times_practiced" in data


# ==================== PROGRESS TESTS ====================

def test_get_progress_overview(client):
    """Test getting learning progress overview"""
    response = client.get("/api/japanese/progress/overview")
    assert response.status_code == 200
    data = response.json()
    assert "progress_percentage" in data
    assert "vocabulary_mastered" in data
    assert "kanji_mastered" in data
    assert "current_streak_days" in data


def test_get_due_reviews(client):
    """Test getting SRS due reviews"""
    response = client.get("/api/japanese/srs/due-reviews")
    assert response.status_code == 200
    data = response.json()
    assert "due_count" in data
    assert "reviews" in data


# ==================== CERTIFICATE TESTS ====================

def test_get_my_certificates(client):
    """Test getting user certificates"""
    response = client.get("/api/japanese/certificates/my-certs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ==================== SUMMARY ====================

def test_japanese_training_module_summary(client):
    """Summary test to verify module is operational"""
    # Test health
    health = client.get("/api/japanese/health")
    assert health.status_code == 200
    
    # Test courses endpoint
    courses = client.get("/api/japanese/courses")
    assert courses.status_code == 200
    
    # Test vocabulary endpoint
    vocab = client.get("/api/japanese/vocabulary/level/N5")
    assert vocab.status_code == 200
    
    # Test progress endpoint
    progress = client.get("/api/japanese/progress/overview")
    assert progress.status_code == 200
    
    print("\n✅ Japanese Training Module: ALL TESTS PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
