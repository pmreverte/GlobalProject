"""
Pytest configuration and shared fixtures.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for testing."""
    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """Create a TestingSessionLocal factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session(engine, TestingSessionLocal):
    """
    Create a fresh database session for each test.
    
    This fixture will create all tables before each test and drop them after,
    ensuring a clean state for each test.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(db_session):
    """Create a test user fixture."""
    from backend.auth.models import User
    user = User(
        username="testuser",
        full_name="Test User",
        role="user",
        is_active=True
    )
    user.set_password("testpass123")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user fixture."""
    from backend.auth.models import User
    admin = User(
        username="admin",
        full_name="Admin User",
        role="superuser",
        is_active=True
    )
    admin.set_password("adminpass123")
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture
def test_llm_config(db_session):
    """Create a test LLM configuration fixture."""
    from backend.auth.models import LLMConfig
    config = LLMConfig(
        name="test-gpt4",
        provider="openai",
        model_name="gpt-4",
        api_key="sk-test123",
        temperature="0.7",
        is_active=True,
        is_default=True
    )
    db_session.add(config)
    db_session.commit()
    return config

@pytest.fixture
def test_document_config(db_session):
    """Create a test document configuration fixture."""
    from backend.auth.models import DocumentConfig
    config = DocumentConfig(
        max_file_size=10,
        allowed_extensions=".pdf,.doc,.docx,.txt",
        max_files_per_upload=5,
        storage_path="test/uploads/",
        is_active=True
    )
    db_session.add(config)
    db_session.commit()
    return config

@pytest.fixture
def test_sql_config(db_session):
    """Create a test SQL configuration fixture."""
    from backend.auth.models import SQLConfig
    config = SQLConfig(
        server="test-server",
        database="test-db",
        username="test-user",
        password="test-pass",
        driver="ODBC Driver 17 for SQL Server",
        use_windows_auth=False,
        is_active=True
    )
    db_session.add(config)
    db_session.commit()
    return config

@pytest.fixture
def test_document_record(db_session, test_user):
    """Create a test document record fixture."""
    from backend.auth.models import DocumentRecord
    doc = DocumentRecord(
        filename="test.pdf",
        file_path="/test/uploads/test.pdf",
        file_size=1024,
        file_type="pdf",
        uploaded_by=test_user.id,
        is_indexed=False,
        is_deleted=False
    )
    db_session.add(doc)
    db_session.commit()
    return doc

@pytest.fixture
def test_document_log(db_session, test_user, test_document_record):
    """Create a test document log fixture."""
    from backend.auth.models import DocumentLog
    log = DocumentLog(
        document_id=test_document_record.id,
        user_id=test_user.id,
        action="upload",
        details="Test upload"
    )
    db_session.add(log)
    db_session.commit()
    return log