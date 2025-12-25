/*
AI Dashboard Widget - Chat System
*/

-- Chat conversations (sessions)
CREATE TABLE IF NOT EXISTS chat_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    title VARCHAR(255),
    language_code VARCHAR(5) DEFAULT 'en' CHECK (language_code IN ('ne', 'en', 'ja')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_conversations_user ON chat_conversations(user_id);
CREATE INDEX idx_chat_conversations_updated ON chat_conversations(updated_at);

-- Individual chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(conversation_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    audio_url VARCHAR(500),  -- For voice messages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_conversation ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);

-- AI widget sessions (track usage for billing)
CREATE TABLE IF NOT EXISTS ai_widget_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),
    session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('text', 'voice', 'avatar')),
    message_count INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    cost_tokens INTEGER DEFAULT 0,  -- For cost tracking
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE INDEX idx_widget_sessions_user ON ai_widget_sessions(user_id);
CREATE INDEX idx_widget_sessions_started ON ai_widget_sessions(started_at);

-- User widget preferences
ALTER TABLE users ADD COLUMN IF NOT EXISTS widget_voice_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS widget_avatar_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS widget_auto_language BOOLEAN DEFAULT TRUE;
