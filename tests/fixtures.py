"""
Test fixtures for Japanese and AI/ML training modules
"""
import pytest
from datetime import datetime
from decimal import Decimal
import uuid

from db_models.user import UserDB
from db_models.japanese_training import (
    JapaneseCourseDB, JapaneseVocabularyDB, JapaneseKanjiDB
)
from db_models.aiml_training import (
    AIMLCourseDB, AIMLLearningPathDB
)
from db_models.i18n import LanguageDB


@pytest.fixture
def test_user(test_db):
    """Create a test user with unique ID and email"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = UserDB(
        user_id=f"user_{unique_id}",
        email=f"test_{unique_id}@example.com",
        hashed_password="$2b$12$test_hash",
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


@pytest.fixture
def test_languages(test_db):
    """Create test languages"""
    languages = [
        LanguageDB(
            language_code="en",
            language_name_en="English",
            language_name_native="English",
            is_active=True,
            display_order=1
        ),
        LanguageDB(
            language_code="ne",
            language_name_en="Nepali",
            language_name_native="नेपाली",
            is_active=True,
            display_order=2
        ),
        LanguageDB(
            language_code="ja",
            language_name_en="Japanese",
            language_name_native="日本語",
            is_active=True,
            display_order=3
        ),
    ]
    for lang in languages:
        test_db.add(lang)
    test_db.commit()
    return languages


@pytest.fixture
def test_japanese_course(test_db):
    """Create a test Japanese course"""
    course = JapaneseCourseDB(
        course_id=uuid.uuid4(),
        course_name="JLPT N5 Beginner",
        jlpt_level="N5",
        jlpt_level_num=5,
        description="Beginner Japanese",
        duration_weeks=12,
        enrollment_fee=Decimal("5000.00"),
        is_active=True
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture
def test_japanese_vocabulary(test_db):
    """Create test vocabulary"""
    vocab = JapaneseVocabularyDB(
        vocab_id=uuid.uuid4(),
        word_kanji="食べる",
        word_hiragana="たべる",
        word_romaji="taberu",
        meaning_en="to eat",
        meaning_ne="खानु",
        jlpt_level="N5",
        word_type="verb",
        example_sentence="りんごを食べる",
        audio_url="https://example.com/audio/taberu.mp3"
    )
    test_db.add(vocab)
    test_db.commit()
    test_db.refresh(vocab)
    return vocab


@pytest.fixture
def test_japanese_kanji(test_db):
    """Create test kanji"""
    kanji = JapaneseKanjiDB(
        kanji_id=uuid.uuid4(),
        character="食",
        meaning_en="eat, food",
        meaning_ne="खाना",
        onyomi="ショク",
        kunyomi="た(べる)",
        jlpt_level="N5",
        stroke_count=9,
        radical="食"
    )
    test_db.add(kanji)
    test_db.commit()
    test_db.refresh(kanji)
    return kanji


@pytest.fixture
def test_aiml_course(test_db):
    """Create a test AI/ML course"""
    course = AIMLCourseDB(
        course_id=uuid.uuid4(),
        course_name="Python for AI",
        course_level="beginner",
        track="ai_fundamentals",
        description="Learn Python for AI",
        duration_weeks=8,
        enrollment_fee=Decimal("10000.00"),
        is_active=True
    )
    test_db.add(course)
    test_db.commit()
    test_db.refresh(course)
    return course


@pytest.fixture
def test_aiml_learning_path(test_db):
    """Create a test learning path"""
    path = AIMLLearningPathDB(
        path_id=uuid.uuid4(),
        path_name="AI Engineer Track",
        description="Complete AI engineer path",
        difficulty_level="intermediate",
        estimated_duration_weeks=24,
        total_fee=Decimal("50000.00"),
        is_active=True
    )
    test_db.add(path)
    test_db.commit()
    test_db.refresh(path)
    return path
