"""
Wallet Management API
Endpoints for wallet operations: topup, balance, transactions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid

from config.database import get_db
from db_models.wallet import (
    UserWallet,
    WalletTransaction,
    TransactionType
)
from services.wallet_service import WalletService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/coaching/wallet", tags=["Coaching Wallet"])


# ==================== PYDANTIC SCHEMAS ====================

class WalletBalanceResponse(BaseModel):
    """Wallet balance response"""
    balance: float
    reserved_balance: float
    available_balance: float
    currency: str
    
    class Config:
        orm_mode = True


class TopupRequest(BaseModel):
    """Topup request model"""
    amount_npr: float = Field(..., gt=0, description="Amount in NPR to top up")
    payment_method_id: str = Field(..., description="Payment method identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount_npr": 1000.00,
                "payment_method_id": "pm_1234567890"
            }
        }


class TopupResponse(BaseModel):
    """Topup response model"""
    transaction_id: str
    amount: float
    bonus_amount: float
    bonus_percentage: float
    total_amount: float
    balance_before: float
    balance_after: float
    bonus_transaction_id: Optional[str] = None


class TransactionResponse(BaseModel):
    """Transaction response model"""
    transaction_id: str
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    session_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


# ==================== API ENDPOINTS ====================

@router.post("/topup", response_model=TopupResponse, status_code=status.HTTP_200_OK)
async def topup_wallet(
    request: TopupRequest,
    db: Session = Depends(get_db)
):
    """
    Top up user wallet with bonus calculation (TEMPORARILY PUBLIC FOR TESTING)
    
    - **amount_npr**: Amount in NPR to top up (must be > 0)
    - **payment_method_id**: Payment method identifier
    
    Bonus tiers:
    - 10% bonus for topups >= NPR 1000
    - 20% bonus for topups >= NPR 2000
    """
    try:
        # TEMPORARY: Use test user for development
        test_user_id = "test_user_001"
        
        result = WalletService.topup(
            db=db,
            user_id=test_user_id,
            amount_npr=Decimal(str(request.amount_npr)),
            payment_method_id=request.payment_method_id
        )
        
        return TopupResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing topup: {str(e)}"
        )


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_wallet_balance(
    db: Session = Depends(get_db)
):
    """
    Get current wallet balance (TEMPORARILY PUBLIC FOR TESTING)
    
    Returns:
    - **balance**: Total wallet balance
    - **reserved_balance**: Amount currently reserved for sessions
    - **available_balance**: Available balance (balance - reserved_balance)
    - **currency**: Currency code (NPR)
    """
    try:
        # TEMPORARY: Use test user for development
        test_user_id = "test_user_001"
        
        # Ensure test wallet exists with initial balance
        wallet = WalletService.get_or_create_wallet(db, test_user_id)
        if wallet.balance == Decimal("0.00"):
            # Initialize test wallet with NPR 1000
            WalletService.topup(
                db=db,
                user_id=test_user_id,
                amount_npr=Decimal("1000.00"),
                payment_method_id="test_init"
            )
        
        balance_data = WalletService.get_balance(
            db=db,
            user_id=test_user_id
        )
        
        return WalletBalanceResponse(**balance_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving balance: {str(e)}"
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_wallet_transactions(
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    db: Session = Depends(get_db)
):
    """
    Get wallet transaction history (TEMPORARILY PUBLIC FOR TESTING)
    
    - **limit**: Number of transactions to return (1-100, default: 50)
    - **offset**: Number of transactions to skip (default: 0)
    - **transaction_type**: Optional filter by type (topup, reserve, charge, refund, bonus)
    
    Returns list of transactions ordered by created_at descending
    """
    try:
        # TEMPORARY: Use test user for development
        test_user_id = "test_user_001"
        
        # Get user wallet
        wallet = WalletService.get_or_create_wallet(db, test_user_id)
        
        # Build query
        query = db.query(WalletTransaction).filter(
            WalletTransaction.wallet_id == wallet.wallet_id
        )
        
        # Apply transaction type filter if provided
        if transaction_type:
            query = query.filter(WalletTransaction.transaction_type == transaction_type)
        
        # Order by created_at descending and apply pagination
        transactions = query.order_by(
            WalletTransaction.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            TransactionResponse(
                transaction_id=str(t.transaction_id),
                transaction_type=t.transaction_type,
                amount=float(t.amount),
                balance_before=float(t.balance_before),
                balance_after=float(t.balance_after),
                session_id=str(t.session_id) if t.session_id else None,
                payment_method_id=t.payment_method_id,
                description=t.description,
                created_at=t.created_at
            )
            for t in transactions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )

