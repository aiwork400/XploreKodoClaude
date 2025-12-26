-- Migration 006: Wallet System for Coaching Platform
-- Tables for user wallets, transactions, voice coaching sessions, video sessions, and assessment results

-- User Wallets
CREATE TABLE user_wallets (
    wallet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) DEFAULT 0.00 NOT NULL,
    reserved_balance DECIMAL(10, 2) DEFAULT 0.00 NOT NULL,
    currency VARCHAR(3) DEFAULT 'NPR' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Wallet Transactions
CREATE TABLE wallet_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES user_wallets(wallet_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'topup', 'reserve', 'charge', 'refund', 'bonus'
    amount DECIMAL(10, 2) NOT NULL,
    balance_before DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    session_id UUID, -- References voice_coaching_sessions or video_sessions
    payment_method_id VARCHAR(255), -- For topup transactions
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Voice Coaching Sessions
CREATE TABLE voice_coaching_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL, -- 'practice', 'assessment', 'live_coaching'
    duration_minutes INTEGER NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'reserved', -- 'reserved', 'active', 'completed', 'cancelled', 'refunded'
    reserved_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    transaction_id UUID REFERENCES wallet_transactions(transaction_id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video Sessions
CREATE TABLE video_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    duration_minutes INTEGER NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'reserved', -- 'reserved', 'active', 'completed', 'cancelled', 'refunded'
    reserved_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    transaction_id UUID REFERENCES wallet_transactions(transaction_id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assessment Results
CREATE TABLE assessment_results (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID REFERENCES voice_coaching_sessions(session_id) ON DELETE SET NULL,
    assessment_type VARCHAR(50) NOT NULL, -- 'pronunciation', 'fluency', 'comprehension', 'overall'
    score DECIMAL(5, 2) NOT NULL, -- 0.00 to 100.00
    feedback TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_user_wallets_user_id ON user_wallets(user_id);
CREATE INDEX idx_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX idx_wallet_transactions_user_id ON wallet_transactions(user_id);
CREATE INDEX idx_wallet_transactions_type ON wallet_transactions(transaction_type);
CREATE INDEX idx_wallet_transactions_created_at ON wallet_transactions(created_at DESC);
CREATE INDEX idx_voice_coaching_sessions_user_id ON voice_coaching_sessions(user_id);
CREATE INDEX idx_voice_coaching_sessions_status ON voice_coaching_sessions(status);
CREATE INDEX idx_voice_coaching_sessions_created_at ON voice_coaching_sessions(created_at DESC);
CREATE INDEX idx_video_sessions_user_id ON video_sessions(user_id);
CREATE INDEX idx_video_sessions_status ON video_sessions(status);
CREATE INDEX idx_video_sessions_created_at ON video_sessions(created_at DESC);
CREATE INDEX idx_assessment_results_user_id ON assessment_results(user_id);
CREATE INDEX idx_assessment_results_session_id ON assessment_results(session_id);
CREATE INDEX idx_assessment_results_type ON assessment_results(assessment_type);

