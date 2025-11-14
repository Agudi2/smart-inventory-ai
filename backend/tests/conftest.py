"""Pytest configuration and fixtures for unit tests."""

import pytest
from sqlalchemy import create_engine, TypeDecorator, CHAR, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects import postgresql
import uuid


# Custom UUID type for SQLite compatibility
class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite compatibility."""
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid=True):
        """Initialize GUID type."""
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(CHAR(36))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not self.as_uuid:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


# Monkey patch PostgreSQL UUID to use GUID for SQLite BEFORE importing models
_original_uuid = postgresql.UUID
postgresql.UUID = GUID

# Now import models after patching
from app.models.base import Base


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for fast unit tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
