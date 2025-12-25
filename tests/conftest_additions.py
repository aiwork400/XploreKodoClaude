"""
Additional fixtures for AI/ML and Japanese training tests
"""
import pytest
import uuid
from decimal import Decimal
from datetime import datetime

from db_models.user import UserDB
from db_models.aiml_training import AIMLCourseDB, AIMLEnrollmentDB
from db_models.japanese_training import JapaneseCourseDB


@pytest.fixture
def test_user(test_db):
    """Create test user 'user_001' that many tests expect"""
    user = UserDB(
        user_id="user_001",
        email="testuser@example.com",
        password_hash="$2b$12$test_hash_here",
        full_name="Test User",
        role="student",
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(autouse=True)
def ensure_test_user(test_db):
    """Auto-create user_001 for all tests that need it"""
    # Check if user exists
    from db_models.user import UserDB
    existing = test_db.query(UserDB).filter(UserDB.user_id == "user_001").first()
    if not existing:
        user = UserDB(
            user_id="user_001",
            email="testuser@example.com",
            password_hash="$2b$12$test_hash",
            full_name="Test User",
            role="student",
            created_at=datetime.utcnow()
        )
        test_db.add(user)
        test_db.commit()
    yield
