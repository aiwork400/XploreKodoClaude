"""
Wallet Service
Business logic for wallet operations: balance management, reservations, transactions
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
import uuid
from datetime import datetime

from db_models.wallet import (
    UserWallet,
    WalletTransaction,
    VoiceCoachingSession,
    TransactionType,
    SessionStatus
)
from config.costs import (
    TOPUP_BONUS_TIER_1_AMOUNT,
    TOPUP_BONUS_TIER_1_PERCENTAGE,
    TOPUP_BONUS_TIER_2_AMOUNT,
    TOPUP_BONUS_TIER_2_PERCENTAGE
)


class WalletService:
    """Service for managing user wallets and transactions"""
    
    @staticmethod
    def get_or_create_wallet(db: Session, user_id: str) -> UserWallet:
        """Get existing wallet or create a new one for the user"""
        wallet = db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
        
        if not wallet:
            wallet = UserWallet(
                wallet_id=uuid.uuid4(),
                user_id=user_id,
                balance=Decimal("0.00"),
                reserved_balance=Decimal("0.00"),
                currency="NPR"
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        
        return wallet
    
    @staticmethod
    def get_balance(db: Session, user_id: str) -> dict:
        """
        Get wallet balance for a user
        
        Returns:
            dict with balance, reserved_balance, available_balance, currency
        """
        wallet = WalletService.get_or_create_wallet(db, user_id)
        
        available_balance = wallet.balance - wallet.reserved_balance
        
        return {
            "balance": float(wallet.balance),
            "reserved_balance": float(wallet.reserved_balance),
            "available_balance": float(available_balance),
            "currency": wallet.currency
        }
    
    @staticmethod
    def reserve_balance(
        db: Session,
        user_id: str,
        amount: Decimal,
        session_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None
    ) -> WalletTransaction:
        """
        Reserve balance for a session
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to reserve
            session_id: Optional session ID
            description: Optional transaction description
            
        Returns:
            WalletTransaction object
            
        Raises:
            ValueError: If insufficient balance
        """
        wallet = WalletService.get_or_create_wallet(db, user_id)
        
        available_balance = wallet.balance - wallet.reserved_balance
        
        if available_balance < amount:
            raise ValueError(f"Insufficient balance. Available: {available_balance}, Required: {amount}")
        
        # Update reserved balance
        balance_before = wallet.reserved_balance
        wallet.reserved_balance += amount
        balance_after = wallet.reserved_balance
        wallet.updated_at = datetime.utcnow()
        
        # Create transaction record
        transaction = WalletTransaction(
            transaction_id=uuid.uuid4(),
            wallet_id=wallet.wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.reserve.value,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            session_id=session_id,
            description=description or f"Reserved {amount} NPR"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def finalize_reservation(
        db: Session,
        user_id: str,
        reserved_amount: Decimal,
        actual_amount: Decimal,
        session_id: uuid.UUID
    ) -> WalletTransaction:
        """
        Finalize a reservation by charging the actual amount
        
        Args:
            db: Database session
            user_id: User ID
            reserved_amount: Amount that was reserved
            actual_amount: Actual amount to charge
            session_id: Session ID
            
        Returns:
            WalletTransaction object for the charge
        """
        wallet = WalletService.get_or_create_wallet(db, user_id)
        
        # Release reserved amount
        if wallet.reserved_balance >= reserved_amount:
            wallet.reserved_balance -= reserved_amount
        else:
            # Handle edge case where reserved balance is less than expected
            wallet.reserved_balance = Decimal("0.00")
        
        # Charge actual amount
        if wallet.balance < actual_amount:
            raise ValueError(f"Insufficient balance. Balance: {wallet.balance}, Required: {actual_amount}")
        
        balance_before = wallet.balance
        wallet.balance -= actual_amount
        balance_after = wallet.balance
        wallet.updated_at = datetime.utcnow()
        
        # Create charge transaction
        transaction = WalletTransaction(
            transaction_id=uuid.uuid4(),
            wallet_id=wallet.wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.charge.value,
            amount=actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            session_id=session_id,
            description=f"Charged {actual_amount} NPR for session"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def refund(
        db: Session,
        user_id: str,
        amount: Decimal,
        session_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None
    ) -> WalletTransaction:
        """
        Refund amount to user wallet
        
        Args:
            db: Database session
            user_id: User ID
            amount: Amount to refund
            session_id: Optional session ID
            description: Optional transaction description
            
        Returns:
            WalletTransaction object
        """
        wallet = WalletService.get_or_create_wallet(db, user_id)
        
        balance_before = wallet.balance
        wallet.balance += amount
        balance_after = wallet.balance
        wallet.updated_at = datetime.utcnow()
        
        transaction = WalletTransaction(
            transaction_id=uuid.uuid4(),
            wallet_id=wallet.wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.refund.value,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            session_id=session_id,
            description=description or f"Refunded {amount} NPR"
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def topup(
        db: Session,
        user_id: str,
        amount_npr: Decimal,
        payment_method_id: str
    ) -> dict:
        """
        Top up wallet with bonus calculation
        
        Args:
            db: Database session
            user_id: User ID
            amount_npr: Amount in NPR to top up
            payment_method_id: Payment method identifier
            
        Returns:
            dict with transaction details and bonus information
        """
        wallet = WalletService.get_or_create_wallet(db, user_id)
        
        # Calculate bonus based on tier
        bonus_amount = Decimal("0.00")
        bonus_percentage = Decimal("0.00")
        
        if amount_npr >= TOPUP_BONUS_TIER_2_AMOUNT:
            bonus_percentage = TOPUP_BONUS_TIER_2_PERCENTAGE
            bonus_amount = (amount_npr * bonus_percentage) / Decimal("100.00")
        elif amount_npr >= TOPUP_BONUS_TIER_1_AMOUNT:
            bonus_percentage = TOPUP_BONUS_TIER_1_PERCENTAGE
            bonus_amount = (amount_npr * bonus_percentage) / Decimal("100.00")
        
        total_amount = amount_npr + bonus_amount
        
        # Update wallet balance
        balance_before = wallet.balance
        wallet.balance += total_amount
        balance_after = wallet.balance
        wallet.updated_at = datetime.utcnow()
        
        # Create topup transaction
        topup_transaction = WalletTransaction(
            transaction_id=uuid.uuid4(),
            wallet_id=wallet.wallet_id,
            user_id=user_id,
            transaction_type=TransactionType.topup.value,
            amount=amount_npr,
            balance_before=balance_before,
            balance_after=balance_after,
            payment_method_id=payment_method_id,
            description=f"Topup of {amount_npr} NPR"
        )
        
        db.add(topup_transaction)
        
        # Create bonus transaction if applicable
        bonus_transaction = None
        if bonus_amount > 0:
            bonus_balance_before = wallet.balance
            # Note: Balance already includes bonus, so we just record it
            bonus_transaction = WalletTransaction(
                transaction_id=uuid.uuid4(),
                wallet_id=wallet.wallet_id,
                user_id=user_id,
                transaction_type=TransactionType.bonus.value,
                amount=bonus_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                payment_method_id=payment_method_id,
                description=f"Bonus {bonus_percentage}% on topup of {amount_npr} NPR"
            )
            db.add(bonus_transaction)
        
        db.commit()
        db.refresh(topup_transaction)
        if bonus_transaction:
            db.refresh(bonus_transaction)
        
        return {
            "transaction_id": str(topup_transaction.transaction_id),
            "amount": float(amount_npr),
            "bonus_amount": float(bonus_amount),
            "bonus_percentage": float(bonus_percentage),
            "total_amount": float(total_amount),
            "balance_before": float(balance_before),
            "balance_after": float(balance_after),
            "bonus_transaction_id": str(bonus_transaction.transaction_id) if bonus_transaction else None
        }

