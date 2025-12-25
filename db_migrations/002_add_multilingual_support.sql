/*
Add multilingual support tables
*/

CREATE TABLE IF NOT EXISTS content_translations (
    translation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL,
    content_id UUID NOT NULL,
    language_code VARCHAR(5) NOT NULL CHECK (language_code IN ('ne', 'en', 'ja')),
    translated_text TEXT NOT NULL,
    audio_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255) REFERENCES users(user_id),
    UNIQUE(content_type, content_id, language_code)
);

CREATE INDEX idx_translations_content ON content_translations(content_type, content_id);
CREATE INDEX idx_translations_language ON content_translations(language_code);

ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(5) DEFAULT 'en' CHECK (preferred_language IN ('ne', 'en', 'ja'));

CREATE TABLE IF NOT EXISTS languages (
    language_code VARCHAR(5) PRIMARY KEY,
    language_name_en VARCHAR(100) NOT NULL,
    language_name_native VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0
);

INSERT INTO languages (language_code, language_name_en, language_name_native, is_active, display_order) VALUES
('en', 'English', 'English', TRUE, 1),
('ne', 'Nepali', 'नेपाली', TRUE, 2),
('ja', 'Japanese', '日本語', TRUE, 3)
ON CONFLICT (language_code) DO NOTHING;