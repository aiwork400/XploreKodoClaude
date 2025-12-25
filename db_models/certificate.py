"""
Database Model - Certificate
"""
from sqlalchemy import Column, String, DateTime
from config.database import Base


class CertificateDB(Base):
    __tablename__ = "certificates"
    
    certificate_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    lesson_id = Column(String, nullable=False, index=True)
    issued_at = Column(DateTime, nullable=False)
