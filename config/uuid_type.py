"""
SQLite-compatible UUID and JSONB types for testing
"""
from sqlalchemy import TypeDecorator, String, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID, JSONB as pgJSONB
import uuid
import json


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.
    
    Uses PostgreSQL UUID for PostgreSQL, String for SQLite.
    """
    impl = String
    cache_ok = True
    
    def __init__(self, as_uuid=True):
        """Initialize UUID type, ignoring as_uuid for SQLite"""
        self.as_uuid = as_uuid
        super().__init__()
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pgUUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)
        else:
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(value)


class JSONB(TypeDecorator):
    """
    Platform-independent JSONB type.
    
    Uses PostgreSQL JSONB for PostgreSQL, Text with JSON serialization for SQLite.
    """
    impl = Text
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pgJSONB())
        else:
            return dialect.type_descriptor(Text())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return json.dumps(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return json.loads(value)
            return value
