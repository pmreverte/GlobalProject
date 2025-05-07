"""
Unit tests for database models.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.db.database import Base
from backend.auth.models import (
    User,
    LLMConfig,
    DocumentConfig,
    SQLConfig,
    DocumentRecord,
    DocumentLog
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# User Model Tests
def test_create_user(db_session):
    """Test creating a new user with all fields."""
    user = User(
        username="testuser",
        full_name="Test User",
        role="user",
        is_active=True
    )
    user.set_password("testpass123")
    
    db_session.add(user)
    db_session.commit()
    
    saved_user = db_session.query(User).first()
    assert saved_user.username == "testuser"
    assert saved_user.full_name == "Test User"
    assert saved_user.role == "user"
    assert saved_user.is_active is True
    assert saved_user.hashed_password.startswith("$2b$")

def test_user_unique_username(db_session):
    """Test that usernames must be unique."""
    user1 = User(username="testuser", full_name="Test User 1")
    user1.set_password("pass123")
    db_session.add(user1)
    db_session.commit()
    
    user2 = User(username="testuser", full_name="Test User 2")
    user2.set_password("pass456")
    db_session.add(user2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_user_password_hashing(db_session):
    """Test that passwords are properly hashed."""
    user = User(username="testuser", full_name="Test User")
    plain_password = "mypassword123"
    user.set_password(plain_password)
    
    assert user.hashed_password != plain_password
    assert user.hashed_password.startswith("$2b$")

def test_user_default_values(db_session):
    """Test default values for user fields."""
    user = User(username="testuser")
    user.set_password("pass123")
    db_session.add(user)
    db_session.commit()
    
    assert user.is_active is True
    assert user.full_name is None

# LLMConfig Model Tests
def test_create_llm_config(db_session):
    """Test creating a new LLM configuration."""
    config = LLMConfig(
        name="test-gpt4",
        provider="openai",
        model_name="gpt-4",
        api_key="sk-test123",
        temperature="0.7"
    )
    
    db_session.add(config)
    db_session.commit()
    
    saved_config = db_session.query(LLMConfig).first()
    assert saved_config.name == "test-gpt4"
    assert saved_config.provider == "openai"
    assert saved_config.model_name == "gpt-4"
    assert saved_config.api_key == "sk-test123"
    assert saved_config.temperature == "0.7"
    assert saved_config.is_active is True
    assert saved_config.is_default is False

# DocumentConfig Model Tests
def test_create_document_config(db_session):
    """Test creating a new document configuration."""
    config = DocumentConfig(
        max_file_size=20,
        allowed_extensions=".pdf,.docx",
        max_files_per_upload=10,
        storage_path="custom/uploads/"
    )
    
    db_session.add(config)
    db_session.commit()
    
    saved_config = db_session.query(DocumentConfig).first()
    assert saved_config.max_file_size == 20
    assert saved_config.allowed_extensions == ".pdf,.docx"
    assert saved_config.max_files_per_upload == 10
    assert saved_config.storage_path == "custom/uploads/"
    assert saved_config.is_active is True
    assert isinstance(saved_config.created_at, datetime)
    assert isinstance(saved_config.updated_at, datetime)

def test_document_config_defaults(db_session):
    """Test default values for document configuration."""
    config = DocumentConfig()
    db_session.add(config)
    db_session.commit()
    
    assert config.max_file_size == 10
    assert config.allowed_extensions == ".pdf,.doc,.docx,.txt"
    assert config.max_files_per_upload == 5
    assert config.storage_path == "uploads/"
    assert config.is_active is True

# SQLConfig Model Tests
def test_create_sql_config(db_session):
    """Test creating a new SQL server configuration."""
    config = SQLConfig(
        server="test-server",
        database="test-db",
        username="test-user",
        password="test-pass",
        driver="ODBC Driver 18 for SQL Server",
        use_windows_auth=False
    )
    
    db_session.add(config)
    db_session.commit()
    
    saved_config = db_session.query(SQLConfig).first()
    assert saved_config.server == "test-server"
    assert saved_config.database == "test-db"
    assert saved_config.username == "test-user"
    assert saved_config.password == "test-pass"
    assert saved_config.driver == "ODBC Driver 18 for SQL Server"
    assert saved_config.use_windows_auth is False
    assert saved_config.is_active is True

def test_sql_config_windows_auth(db_session):
    """Test SQL configuration with Windows authentication."""
    config = SQLConfig(
        server="test-server",
        database="test-db",
        use_windows_auth=True
    )
    
    db_session.add(config)
    db_session.commit()
    
    saved_config = db_session.query(SQLConfig).first()
    assert saved_config.username is None
    assert saved_config.password is None
    assert saved_config.use_windows_auth is True

# DocumentRecord and DocumentLog Tests
def test_document_record_with_user(db_session):
    """Test creating a document record with user relationship."""
    # Create a user first
    user = User(username="testuser", full_name="Test User")
    user.set_password("pass123")
    db_session.add(user)
    db_session.commit()
    
    # Create a document record
    doc = DocumentRecord(
        filename="test.pdf",
        file_path="/uploads/test.pdf",
        file_size=1024,
        file_type="pdf",
        uploaded_by=user.id
    )
    
    db_session.add(doc)
    db_session.commit()
    
    # Test the relationship
    assert doc.user.username == "testuser"
    assert doc.is_indexed is False
    assert doc.is_deleted is False
    assert isinstance(doc.upload_date, datetime)
    assert isinstance(doc.last_modified, datetime)

def test_document_log_relationships(db_session):
    """Test document log relationships with user and document."""
    # Create user and document
    user = User(username="testuser", full_name="Test User")
    user.set_password("pass123")
    db_session.add(user)
    db_session.commit()
    
    doc = DocumentRecord(
        filename="test.pdf",
        file_path="/uploads/test.pdf",
        file_size=1024,
        file_type="pdf",
        uploaded_by=user.id
    )
    db_session.add(doc)
    db_session.commit()
    
    # Create log entry
    log = DocumentLog(
        document_id=doc.id,
        user_id=user.id,
        action="upload",
        details="Initial upload"
    )
    
    db_session.add(log)
    db_session.commit()
    
    # Test relationships
    assert log.user.username == "testuser"
    assert log.document.filename == "test.pdf"
    assert isinstance(log.timestamp, datetime)
    assert log.action == "upload"
    assert log.details == "Initial upload"