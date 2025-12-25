"""
AI Dashboard Widget API
Real-time chat with AI assistant in multiple languages
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from models.ai_widget import (
    ChatMessageCreate, ChatMessageResponse, ChatConversationCreate,
    ChatConversationResponse, ChatConversationWithMessages,
    WidgetSettingsUpdate, WidgetSettingsResponse,
    AIWidgetSessionCreate, AIWidgetSessionResponse,
    ChatRequest, ChatResponse
)
from db_models.ai_widget import ChatConversationDB, ChatMessageDB, AIWidgetSessionDB
from db_models.user import UserDB
from config.database import get_db
from config.dependencies import get_current_user
from services.ai_service import AIService

router = APIRouter(prefix="/api/ai-widget", tags=["AI Widget"])


@router.post("/conversations", response_model=ChatConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ChatConversationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat conversation"""
    
    new_conversation = ChatConversationDB(
        conversation_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        title=conversation.title,
        language_code=conversation.language_code,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return ChatConversationResponse(
        conversation_id=str(new_conversation.conversation_id),
        user_id=new_conversation.user_id,
        title=new_conversation.title,
        language_code=new_conversation.language_code,
        created_at=new_conversation.created_at,
        updated_at=new_conversation.updated_at
    )


@router.get("/conversations", response_model=List[ChatConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all conversations for current user"""
    
    conversations = db.query(ChatConversationDB).filter(
        ChatConversationDB.user_id == current_user["user_id"]
    ).order_by(ChatConversationDB.updated_at.desc()).all()
    
    return [
        ChatConversationResponse(
            conversation_id=str(conv.conversation_id),
            user_id=conv.user_id,
            title=conv.title,
            language_code=conv.language_code,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ChatConversationWithMessages)
async def get_conversation_with_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get conversation with all messages"""
    
    conversation = db.query(ChatConversationDB).filter(
        ChatConversationDB.conversation_id == uuid.UUID(conversation_id),
        ChatConversationDB.user_id == current_user["user_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = db.query(ChatMessageDB).filter(
        ChatMessageDB.conversation_id == uuid.UUID(conversation_id)
    ).order_by(ChatMessageDB.created_at.asc()).all()
    
    return ChatConversationWithMessages(
        conversation_id=str(conversation.conversation_id),
        title=conversation.title,
        language_code=conversation.language_code,
        messages=[
            ChatMessageResponse(
                message_id=str(msg.message_id),
                conversation_id=str(msg.conversation_id),
                role=msg.role,
                content=msg.content,
                audio_url=msg.audio_url,
                created_at=msg.created_at
            )
            for msg in messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send a message and get AI response"""
    
    # Get or create conversation
    if request.conversation_id:
        conversation = db.query(ChatConversationDB).filter(
            ChatConversationDB.conversation_id == uuid.UUID(request.conversation_id),
            ChatConversationDB.user_id == current_user["user_id"]
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        language = request.language or current_user.get("preferred_language", "en")
        title = await AIService.generate_conversation_title(request.message, language)
        
        conversation = ChatConversationDB(
            conversation_id=uuid.uuid4(),
            user_id=current_user["user_id"],
            title=title,
            language_code=language,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Save user message
    user_message = ChatMessageDB(
        message_id=uuid.uuid4(),
        conversation_id=conversation.conversation_id,
        role="user",
        content=request.message,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    
    # Get conversation history
    messages = db.query(ChatMessageDB).filter(
        ChatMessageDB.conversation_id == conversation.conversation_id
    ).order_by(ChatMessageDB.created_at.asc()).all()
    
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    
    # Get AI response
    try:
        ai_content, tokens = await AIService.chat(
            messages=message_history,
            language=conversation.language_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    
    # Save AI response
    ai_message = ChatMessageDB(
        message_id=uuid.uuid4(),
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=ai_content,
        created_at=datetime.utcnow()
    )
    db.add(ai_message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(ai_message)
    
    return ChatResponse(
        conversation_id=str(conversation.conversation_id),
        message_id=str(ai_message.message_id),
        content=ai_content,
        audio_url=None,
        language=conversation.language_code,
        tokens_used=tokens
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation"""
    
    conversation = db.query(ChatConversationDB).filter(
        ChatConversationDB.conversation_id == uuid.UUID(conversation_id),
        ChatConversationDB.user_id == current_user["user_id"]
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return None


@router.put("/settings", response_model=WidgetSettingsResponse)
async def update_widget_settings(
    settings: WidgetSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update AI widget settings"""
    
    user = db.query(UserDB).filter(UserDB.user_id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if settings.widget_voice_enabled is not None:
        user.widget_voice_enabled = settings.widget_voice_enabled
    if settings.widget_avatar_enabled is not None:
        user.widget_avatar_enabled = settings.widget_avatar_enabled
    if settings.widget_auto_language is not None:
        user.widget_auto_language = settings.widget_auto_language
    
    db.commit()
    db.refresh(user)
    
    return WidgetSettingsResponse(
        widget_voice_enabled=user.widget_voice_enabled,
        widget_avatar_enabled=user.widget_avatar_enabled,
        widget_auto_language=user.widget_auto_language,
        preferred_language=user.preferred_language
    )


@router.get("/settings", response_model=WidgetSettingsResponse)
async def get_widget_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get AI widget settings"""
    
    user = db.query(UserDB).filter(UserDB.user_id == current_user["user_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return WidgetSettingsResponse(
        widget_voice_enabled=user.widget_voice_enabled,
        widget_avatar_enabled=user.widget_avatar_enabled,
        widget_auto_language=user.widget_auto_language,
        preferred_language=user.preferred_language
    )


@router.post("/sessions", response_model=AIWidgetSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_widget_session(
    session: AIWidgetSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new AI widget session (for tracking usage)"""
    
    new_session = AIWidgetSessionDB(
        session_id=uuid.uuid4(),
        user_id=current_user["user_id"],
        session_type=session.session_type,
        message_count=0,
        duration_seconds=0,
        cost_tokens=0,
        started_at=datetime.utcnow()
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return AIWidgetSessionResponse(
        session_id=str(new_session.session_id),
        session_type=new_session.session_type,
        message_count=new_session.message_count,
        duration_seconds=new_session.duration_seconds,
        cost_tokens=new_session.cost_tokens,
        started_at=new_session.started_at,
        ended_at=new_session.ended_at
    )
