"""
Payment API Endpoints
Stripe payment integration
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from typing import List
import stripe

from models.payment import PaymentIntentCreate, PaymentIntentResponse, PaymentRecord, PaymentStatusResponse
from config.dependencies import get_current_user
from config.stripe_config import STRIPE_SECRET_KEY

router = APIRouter(prefix="/api/payments", tags=["payments"])

# In-memory payment storage (will be replaced with database later)
payments_db = {}


@router.post("/create-intent", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Stripe payment intent
    
    - Authenticated users can create payment intents
    - Returns client_secret for frontend to complete payment
    - Validates amount and currency
    """
    try:
        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            metadata={
                "user_id": current_user.get("user_id"),
                "email": current_user.get("email")
            }
        )
        
        # Store payment record
        payment_record = PaymentRecord(
            payment_intent_id=intent.id,
            user_id=current_user.get("user_id"),
            amount=payment_data.amount,
            currency=payment_data.currency,
            status=intent.status,
            description=payment_data.description,
            created_at=datetime.utcnow()
        )
        payments_db[intent.id] = payment_record
        
        return PaymentIntentResponse(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )


@router.get("/my-payments", response_model=List[PaymentRecord])
async def get_my_payments(current_user: dict = Depends(get_current_user)):
    """
    Get current user's payment history
    
    - Returns list of all payments for the authenticated user
    - Only returns user's own payments
    """
    user_id = current_user.get("user_id")
    
    # Filter payments by user_id
    user_payments = [
        payment
        for payment in payments_db.values()
        if payment.user_id == user_id
    ]
    
    return user_payments


@router.get("/status/{payment_intent_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_intent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get payment status by ID
    
    - Returns current status of a payment intent
    - User can only check their own payments
    """
    # Check if payment exists in our records
    payment_record = payments_db.get(payment_intent_id)
    
    if not payment_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Verify user owns this payment
    if payment_record.user_id != current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )
    
    try:
        # Get latest status from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Update our record
        payment_record.status = intent.status
        payments_db[payment_intent_id] = payment_record
        
        return PaymentStatusResponse(
            payment_intent_id=intent.id,
            status=intent.status,
            amount=intent.amount,
            currency=intent.currency,
            description=payment_record.description
        )
    
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}"
        )
