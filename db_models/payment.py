"""
Database Model - Payment
"""
from sqlalchemy import Column, String, DateTime, Float
from config.database import Base


class PaymentDB(Base):
    __tablename__ = "payments"
    
    payment_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    payment_intent_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
