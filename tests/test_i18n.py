"""
Tests for Internationalization (i18n) API
Testing multilingual support with 3 languages: Nepali, English, Japanese
"""
import pytest
from fastapi.testclient import TestClient


class TestLanguagesList:
    """Test getting available languages"""
    
    def test_get_languages_list(self, client):
        """Test getting list of available languages"""
        response = client.get("/api/i18n/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3  # Nepali, English, Japanese
        
        # Check all 3 languages are present
        language_codes = [lang["language_code"] for lang in data]
        assert "en" in language_codes
        assert "ne" in language_codes
        assert "ja" in language_codes
    
    def test_languages_have_native_names(self, client):
        """Test that languages include native names"""
        response = client.get("/api/i18n/languages")
        
        data = response.json()
        
        # Find each language and check native name
        en_lang = next(l for l in data if l["language_code"] == "en")
        assert en_lang["language_name_native"] == "English"
        
        ne_lang = next(l for l in data if l["language_code"] == "ne")
        assert "नेपाली" in ne_lang["language_name_native"]
        
        ja_lang = next(l for l in data if l["language_code"] == "ja")
        assert "日本語" in ja_lang["language_name_native"]


class TestTranslationCreation:
    """Test creating translations"""
    
    def test_create_translation_as_admin(self, client):
        """Test admin can create translations"""
        # Register admin
        client.post("/api/auth/register", json={
            "email": "admin@test.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin@test.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        # Create a lesson first
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
        
        # Create translation in Nepali
        response = client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "ne",
                "translated_text": "परीक्षण पाठ"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["language_code"] == "ne"
        assert data["translated_text"] == "परीक्षण पाठ"
    
    def test_create_translation_requires_admin(self, client):
        """Test that only admins can create translations"""
        # Register student
        client.post("/api/auth/register", json={
            "email": "student@test.com",
            "password": "StudentPass123!",
            "role": "student"
        })
        student_login = client.post("/api/auth/login", json={
            "email": "student@test.com",
            "password": "StudentPass123!"
        })
        student_token = student_login.json()["access_token"]
        
        # Try to create translation
        response = client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": "00000000-0000-0000-0000-000000000001",
                "language_code": "ne",
                "translated_text": "Test"
            },
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403
    
    def test_cannot_duplicate_translation(self, client):
        """Test that duplicate translations are prevented"""
        # Setup admin and lesson
        client.post("/api/auth/register", json={
            "email": "admin2@test.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin2@test.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Create first translation
        client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "ja",
                "translated_text": "テストレッスン"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to create duplicate
        response = client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "ja",
                "translated_text": "別のテスト"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400


class TestTranslationRetrieval:
    """Test retrieving translations"""
    
    def test_get_content_in_specific_language(self, client):
        """Test getting content in user's preferred language"""
        # Setup
        client.post("/api/auth/register", json={
            "email": "admin3@test.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin3@test.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "English Title", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Add translations
        client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "en",
                "translated_text": "English Lesson"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "ne",
                "translated_text": "नेपाली पाठ"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Get in Nepali
        response = client.get(
            f"/api/i18n/content/lesson/{lesson_id}?language=ne",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "ne"
        assert data["text"] == "नेपाली पाठ"
    
    def test_fallback_to_english_if_language_unavailable(self, client):
        """Test fallback to English if requested language not available"""
        # Setup
        client.post("/api/auth/register", json={
            "email": "admin4@test.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin4@test.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Add only English translation
        client.post(
            "/api/i18n/translations",
            json={
                "content_type": "lesson",
                "content_id": lesson_id,
                "language_code": "en",
                "translated_text": "English Only"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Request in Japanese (not available)
        response = client.get(
            f"/api/i18n/content/lesson/{lesson_id}?language=ja",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"  # Fallback to English
        assert data["text"] == "English Only"
    
    def test_get_all_translations_for_content(self, client):
        """Test getting all available translations"""
        # Setup
        client.post("/api/auth/register", json={
            "email": "admin5@test.com",
            "password": "AdminPass123!",
            "role": "admin"
        })
        admin_login = client.post("/api/auth/login", json={
            "email": "admin5@test.com",
            "password": "AdminPass123!"
        })
        admin_token = admin_login.json()["access_token"]
        
        lesson_response = client.post(
            "/api/lessons",
            json={"level": "N5", "title": "Test", "description": "Test", "content_json": {}},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        lesson_id = lesson_response.json()["lesson_id"]
        
        # Add all 3 translations
        for lang, text in [("en", "English"), ("ne", "नेपाली"), ("ja", "日本語")]:
            client.post(
                "/api/i18n/translations",
                json={
                    "content_type": "lesson",
                    "content_id": lesson_id,
                    "language_code": lang,
                    "translated_text": text
                },
                headers={"Authorization": f"Bearer {admin_token}"}
            )
        
        # Get all translations
        response = client.get(
            f"/api/i18n/content/lesson/{lesson_id}/all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 3
        assert "en" in data["translations"]
        assert "ne" in data["translations"]
        assert "ja" in data["translations"]


class TestUserLanguagePreference:
    """Test user language preference management"""
    
    def test_set_user_language_preference(self, client):
        """Test user can set their language preference"""
        # Register user
        client.post("/api/auth/register", json={
            "email": "user@test.com",
            "password": "UserPass123!",
            "role": "student"
        })
        user_login = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "UserPass123!"
        })
        user_token = user_login.json()["access_token"]
        
        # Set preference to Nepali
        response = client.put(
            "/api/i18n/user/language-preference",
            json={"preferred_language": "ne"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "ne"
    
    def test_get_user_language_preference(self, client):
        """Test getting user's language preference"""
        # Register user
        client.post("/api/auth/register", json={
            "email": "user2@test.com",
            "password": "UserPass123!",
            "role": "student"
        })
        user_login = client.post("/api/auth/login", json={
            "email": "user2@test.com",
            "password": "UserPass123!"
        })
        user_token = user_login.json()["access_token"]
        
        # Set to Japanese
        client.put(
            "/api/i18n/user/language-preference",
            json={"preferred_language": "ja"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Get preference
        response = client.get(
            "/api/i18n/user/language-preference",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "ja"
