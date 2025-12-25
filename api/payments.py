"""
Payment Processing API - Database Version
Stripe payment integration with PostgreSQL
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import stripe

from models.payment import PaymentIntentCreate, PaymentIntentResponse, PaymentHistoryResponse
from db_models.payment import PaymentDB
from config.database import get_db
from config.dependencies import get_current_user
from config.stripe_config import get_stripe_key

router = APIRouter(prefix="/api/payments", tags=["Payments"])

# Configure Stripe
stripe.api_key = get_stripe_key()


@router.post("/create-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe payment intent and store in PostgreSQL"""
    
    # Validate amount
    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    try:
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(payment_data.amount * 100),  # Convert to cents
            currency=payment_data.currency,
            metadata={"user_id": current_user["user_id"]}
        )
        
        # Store in database
        payment_id = str(uuid.uuid4())
        
        new_payment = PaymentDB(
            payment_id=payment_id,
            user_id=current_user["user_id"],
            payment_intent_id=intent.id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=intent.status,
            created_at=datetime.utcnow()
        )
        
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        
        return PaymentIntentResponse(
            payment_id=new_payment.payment_id,
            payment_intent_id=new_payment.payment_intent_id,
            client_secret=intent.client_secret,
            amount=new_payment.amount,
            currency=new_payment.currency,
            status=new_payment.status
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.get("/my-payments", response_model=list[PaymentHistoryResponse])
async def get_my_payment_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get payment history for current user from PostgreSQL"""
    payments = db.query(PaymentDB).filter(
        PaymentDB.user_id == current_user["user_id"]
    ).all()
    
    return [
        PaymentHistoryResponse(
            payment_id=payment.payment_id,
            payment_intent_id=payment.payment_intent_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            created_at=payment.created_at
        )
        for payment in payments
    ]


@router.get("/status/{payment_intent_id}", response_model=PaymentHistoryResponse)
async def get_payment_status(
    payment_intent_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get status of a specific payment from PostgreSQL"""
    payment = db.query(PaymentDB).filter(
        PaymentDB.payment_intent_id == payment_intent_id,
        PaymentDB.user_id == current_user["user_id"]
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentHistoryResponse(
        payment_id=payment.payment_id,
        payment_intent_id=payment.payment_intent_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        created_at=payment.created_at
    )
