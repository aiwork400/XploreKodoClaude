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
    """Create test user with unique ID and email"""
    unique_id = str(uuid.uuid4())[:8]
    user = UserDB(
        user_id=f"user_{unique_id}",
        email=f"testuser_{unique_id}@example.com",
        hashed_password="$2b$12$test_hash_here",
        role="student",
        preferred_language="en",
        widget_voice_enabled=False,
        widget_avatar_enabled=False,
        widget_auto_language=True,
        created_at=datetime.utcnow()
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(autouse=True)
def ensure_test_user(test_db):
    """Auto-create user_001 for all tests that need it (if not exists)"""
    # Check if user exists
    from db_models.user import UserDB, UserRole
    existing = test_db.query(UserDB).filter(UserDB.user_id == "user_001").first()
    if not existing:
        user = UserDB(
            user_id="user_001",
            email="testuser_001@example.com",
            hashed_password="$2b$12$test_hash",
            role=UserRole.student,
            preferred_language="en",
            widget_voice_enabled=False,
            widget_avatar_enabled=False,
            widget_auto_language=True,
            created_at=datetime.utcnow()
        )
        test_db.add(user)
        test_db.commit()
    yield
