"""
Database Models - Wallet System
SQLAlchemy models for wallet, transactions, and coaching sessions
"""
from sqlalchemy import Column, String, Integer, DECIMAL, Text, TIMESTAMP, ForeignKey
from config.uuid_type import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from config.database import Base


class TransactionType(str, enum.Enum):
    """Wallet transaction types"""
    topup = "topup"
    reserve = "reserve"
    charge = "charge"
    refund = "refund"
    bonus = "bonus"


class VoiceCoachingMode(str, enum.Enum):
    """Voice coaching session modes"""
    practice = "practice"
    assessment = "assessment"
    live_coaching = "live_coaching"


class SessionStatus(str, enum.Enum):
    """Session status values"""
    reserved = "reserved"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"


class UserWallet(Base):
    """User wallet model"""
    __tablename__ = "user_wallets"
    
    wallet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    reserved_balance = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="NPR")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")


class WalletTransaction(Base):
    """Wallet transaction model"""
    __tablename__ = "wallet_transactions"
    
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("user_wallets.wallet_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    balance_before = Column(DECIMAL(10, 2), nullable=False)
    balance_after = Column(DECIMAL(10, 2), nullable=False)
    session_id = Column(UUID(as_uuid=True))  # Can reference voice or video sessions
    payment_method_id = Column(String(255))  # For topup transactions
    description = Column(Text)
    transaction_metadata = Column("metadata", JSONB)  # Column name is 'metadata' in DB
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    # Relationships
    wallet = relationship("UserWallet", back_populates="transactions")


class VoiceCoachingSession(Base):
    """Voice coaching session model"""
    __tablename__ = "voice_coaching_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    mode = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    cost = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="reserved", index=True)
    reserved_at = Column(TIMESTAMP)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("wallet_transactions.transaction_id"))
    voice_session_metadata = Column("metadata", JSONB)  # Column name is 'metadata' in DB
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)


class VideoSession(Base):
    """Video session model"""
    __tablename__ = "video_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False)
    cost = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="reserved", index=True)
    reserved_at = Column(TIMESTAMP)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("wallet_transactions.transaction_id"))
    video_session_metadata = Column("metadata", JSONB)  # Column name is 'metadata' in DB
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)


class AssessmentResult(Base):
    """Assessment result model"""
    __tablename__ = "assessment_results"
    
    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("voice_coaching_sessions.session_id", ondelete="SET NULL"), index=True)
    assessment_type = Column(String(50), nullable=False, index=True)
    score = Column(DECIMAL(5, 2), nullable=False)  # 0.00 to 100.00
    feedback = Column(Text)
    details = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=func.now())

