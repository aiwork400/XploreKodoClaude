"""
Payment Models (Pydantic)
Request/Response schemas for API
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PaymentIntentCreate(BaseModel):
    amount: float
    currency: str = "usd"


class PaymentIntentResponse(BaseModel):
    payment_id: str
    payment_intent_id: str
    client_secret: str
    amount: float
    currency: str
    status: str


class PaymentHistoryResponse(BaseModel):
    payment_id: str
    payment_intent_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentRecord(BaseModel):
    payment_id: str
    user_id: str
    payment_intent_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
