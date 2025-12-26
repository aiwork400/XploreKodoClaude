"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from config.database import Base, get_db

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before running tests"""
    # Import all model modules to register them with Base
    import db_models.user
    import db_models.lesson
    import db_models.progress
    import db_models.enrollment
    import db_models.quiz
    import db_models.payment
    import db_models.certificate
    import db_models.i18n
    import db_models.ai_widget
    import db_models.japanese_training
    import db_models.aiml_training
    import db_models.wallet
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Seed initial data for languages (required for i18n tests)
    db = TestingSessionLocal()
    try:
        from db_models.i18n import LanguageDB
        if db.query(LanguageDB).count() == 0:
            languages = [
                LanguageDB(language_code="en", language_name_en="English", 
                          language_name_native="English", is_active=True, display_order=1),
                LanguageDB(language_code="ne", language_name_en="Nepali", 
                          language_name_native="ÃƒÂ Ã‚Â¤Ã‚Â¨ÃƒÂ Ã‚Â¥Ã¢â‚¬Â¡ÃƒÂ Ã‚Â¤Ã‚ÂªÃƒÂ Ã‚Â¤Ã‚Â¾ÃƒÂ Ã‚Â¤Ã‚Â²ÃƒÂ Ã‚Â¥Ã¢â€šÂ¬", is_active=True, display_order=2),
                LanguageDB(language_code="ja", language_name_en="Japanese", 
                          language_name_native="ÃƒÂ¦Ã¢â‚¬â€Ã‚Â¥ÃƒÂ¦Ã…â€œÃ‚Â¬ÃƒÂ¨Ã‚ÂªÃ…Â¾", is_active=True, display_order=3),
            ]
            db.add_all(languages)
            db.commit()
    except Exception as e:
        print(f"Warning: Could not seed languages: {e}")
        db.rollback()
    finally:
        db.close()
    
    yield
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    """Clear all data between tests but keep schema"""
    yield
    # Clean up data after each test
    db = TestingSessionLocal()
    try:
        # Skip language table cleanup (needed for i18n tests)
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != 'languages':
                db.execute(table.delete())
        db.commit()
    except Exception as e:
        print(f"Warning during cleanup: {e}")
        db.rollback()
    finally:
        db.close()


@pytest.fixture
def client():
    """Test client with database override"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_db():
    """Direct database session for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Auto-imported additions
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
    import uuid
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
    from db_models.user import UserDB, UserRole
    from datetime import datetime
    
    # Check if user_001 exists, create if not
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
