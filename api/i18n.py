"""
Internationalization (i18n) API
Endpoints for multilingual content management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import uuid
from datetime import datetime

from models.i18n import (
    LanguageInfo, TranslationCreate, TranslationUpdate, 
    TranslationResponse, ContentTranslations, UserLanguagePreference,
    MultilingualContent
)
from db_models.i18n import ContentTranslationDB, LanguageDB
from db_models.user import UserDB
from config.database import get_db
from config.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/api/i18n", tags=["Internationalization"])


@router.get("/languages", response_model=List[LanguageInfo])
async def get_available_languages(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of available languages"""
    query = db.query(LanguageDB)
    
    if active_only:
        query = query.filter(LanguageDB.is_active == True)
    
    languages = query.order_by(LanguageDB.display_order).all()
    
    return [
        LanguageInfo(
            language_code=lang.language_code,
            language_name_en=lang.language_name_en,
            language_name_native=lang.language_name_native,
            is_active=lang.is_active,
            display_order=lang.display_order
        )
        for lang in languages
    ]


@router.post("/translations", response_model=TranslationResponse, status_code=status.HTTP_201_CREATED)
async def create_translation(
    translation: TranslationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new content translation (admin only)"""
    
    # Check if translation already exists
    existing = db.query(ContentTranslationDB).filter(
        ContentTranslationDB.content_type == translation.content_type,
        ContentTranslationDB.content_id == uuid.UUID(translation.content_id),
        ContentTranslationDB.language_code == translation.language_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation already exists for this content in {translation.language_code}"
        )
    
    # Create new translation
    new_translation = ContentTranslationDB(
        translation_id=uuid.uuid4(),
        content_type=translation.content_type,
        content_id=uuid.UUID(translation.content_id),
        language_code=translation.language_code,
        translated_text=translation.translated_text,
        audio_url=translation.audio_url,
        updated_by=current_user["user_id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_translation)
    db.commit()
    db.refresh(new_translation)
    
    return TranslationResponse(
        translation_id=str(new_translation.translation_id),
        content_type=new_translation.content_type,
        content_id=str(new_translation.content_id),
        language_code=new_translation.language_code,
        translated_text=new_translation.translated_text,
        audio_url=new_translation.audio_url,
        created_at=new_translation.created_at,
        updated_at=new_translation.updated_at
    )


@router.get("/content/{content_type}/{content_id}", response_model=MultilingualContent)
async def get_translated_content(
    content_type: str,
    content_id: str,
    language: str = Query(default="en", regex="^(ne|en|ja)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get content in specified language"""
    
    translation = db.query(ContentTranslationDB).filter(
        ContentTranslationDB.content_type == content_type,
        ContentTranslationDB.content_id == uuid.UUID(content_id),
        ContentTranslationDB.language_code == language
    ).first()
    
    if not translation:
        # Fallback to English if requested language not available
        if language != "en":
            translation = db.query(ContentTranslationDB).filter(
                ContentTranslationDB.content_type == content_type,
                ContentTranslationDB.content_id == uuid.UUID(content_id),
                ContentTranslationDB.language_code == "en"
            ).first()
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No translation found for {content_type} {content_id}"
            )
    
    return MultilingualContent(
        content_id=str(translation.content_id),
        content_type=translation.content_type,
        language=translation.language_code,
        text=translation.translated_text,
        audio_url=translation.audio_url
    )


@router.get("/content/{content_type}/{content_id}/all", response_model=ContentTranslations)
async def get_all_translations(
    content_type: str,
    content_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all translations for a piece of content"""
    
    translations = db.query(ContentTranslationDB).filter(
        ContentTranslationDB.content_type == content_type,
        ContentTranslationDB.content_id == uuid.UUID(content_id)
    ).all()
    
    if not translations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No translations found for {content_type} {content_id}"
        )
    
    translations_dict = {
        t.language_code: t.translated_text
        for t in translations
    }
    
    return ContentTranslations(
        content_id=content_id,
        content_type=content_type,
        translations=translations_dict
    )


@router.put("/translations/{translation_id}", response_model=TranslationResponse)
async def update_translation(
    translation_id: str,
    update: TranslationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update an existing translation (admin only)"""
    
    translation = db.query(ContentTranslationDB).filter(
        ContentTranslationDB.translation_id == uuid.UUID(translation_id)
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found"
        )
    
    # Update fields
    if update.translated_text is not None:
        translation.translated_text = update.translated_text
    if update.audio_url is not None:
        translation.audio_url = update.audio_url
    
    translation.updated_at = datetime.utcnow()
    translation.updated_by = current_user["user_id"]
    
    db.commit()
    db.refresh(translation)
    
    return TranslationResponse(
        translation_id=str(translation.translation_id),
        content_type=translation.content_type,
        content_id=str(translation.content_id),
        language_code=translation.language_code,
        translated_text=translation.translated_text,
        audio_url=translation.audio_url,
        created_at=translation.created_at,
        updated_at=translation.updated_at
    )


@router.put("/user/language-preference", response_model=dict)
async def update_user_language_preference(
    preference: UserLanguagePreference,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update user's language preference"""
    
    user = db.query(UserDB).filter(UserDB.user_id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.preferred_language = preference.preferred_language
    db.commit()
    
    return {
        "message": "Language preference updated",
        "preferred_language": preference.preferred_language
    }


@router.get("/user/language-preference", response_model=UserLanguagePreference)
async def get_user_language_preference(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's language preference"""
    
    user = db.query(UserDB).filter(UserDB.user_id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserLanguagePreference(
        preferred_language=user.preferred_language or "en"
    )


@router.delete("/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation(
    translation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a translation (admin only)"""
    
    translation = db.query(ContentTranslationDB).filter(
        ContentTranslationDB.translation_id == uuid.UUID(translation_id)
    ).first()
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Translation not found"
        )
    
    db.delete(translation)
    db.commit()
    
    return None
