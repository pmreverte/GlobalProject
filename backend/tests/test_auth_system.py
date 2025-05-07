"""
Unit tests for the authentication system module.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from fastapi import HTTPException
from jose import jwt

from backend.auth.auth_system import (
    create_access_token,
    authenticate_user,
    get_user,
    is_superuser,
    SECRET_KEY,
    ALGORITHM
)
from backend.auth.models import User as DBUser

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"
TEST_ROLE = "user"

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return Mock()

@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = Mock(spec=DBUser)
    user.username = TEST_USERNAME
    user.role = TEST_ROLE
    user.is_active = True
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGpJ4vZKkyu"  # hashed 'testpass'
    return user

def test_get_user_found(mock_db_session, mock_user):
    """Test getting an existing user."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    result = get_user(TEST_USERNAME, mock_db_session)
    
    assert result == mock_user
    mock_db_session.query.assert_called_once()

def test_get_user_not_found(mock_db_session):
    """Test getting a non-existent user."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = get_user("nonexistent", mock_db_session)
    
    assert result is None
    mock_db_session.query.assert_called_once()

def test_authenticate_user_success(mock_db_session, mock_user):
    """Test successful user authentication."""
    with patch('backend.auth.auth_system.verify_password', return_value=True):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = authenticate_user(TEST_USERNAME, TEST_PASSWORD, mock_db_session)
        
        assert result == mock_user

def test_authenticate_user_wrong_password(mock_db_session, mock_user):
    """Test authentication with wrong password."""
    with patch('backend.auth.auth_system.verify_password', return_value=False):
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = authenticate_user(TEST_USERNAME, "wrongpass", mock_db_session)
        
        assert result is None

def test_authenticate_user_not_found(mock_db_session):
    """Test authentication with non-existent user."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    result = authenticate_user("nonexistent", TEST_PASSWORD, mock_db_session)
    
    assert result is None

def test_create_access_token_success():
    """Test successful token creation."""
    test_data = {
        "sub": TEST_USERNAME,
        "role": TEST_ROLE
    }
    
    token = create_access_token(test_data)
    
    # Verify token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == TEST_USERNAME
    assert payload["role"] == TEST_ROLE
    assert "exp" in payload
    assert "iat" in payload
    assert payload["type"] == "access_token"

def test_create_access_token_with_expiry():
    """Test token creation with custom expiry time."""
    test_data = {
        "sub": TEST_USERNAME,
        "role": TEST_ROLE
    }
    expires_delta = timedelta(minutes=30)
    
    token = create_access_token(test_data, expires_delta)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    now = datetime.now(timezone.utc)
    token_exp = datetime.fromtimestamp(payload["exp"], timezone.utc)
    # Allow 5 second tolerance for test execution time
    assert abs((token_exp - now - expires_delta).total_seconds()) < 5

def test_create_access_token_missing_claims():
    """Test token creation with missing required claims."""
    test_data = {"sub": TEST_USERNAME}  # Missing role
    
    with pytest.raises(ValueError, match="El token debe contener 'sub' y 'role'"):
        create_access_token(test_data)

def test_is_superuser_true():
    """Test superuser check with superuser token."""
    token_data = {
        "sub": TEST_USERNAME,
        "role": "superuser",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    assert is_superuser(token) is True

def test_is_superuser_false():
    """Test superuser check with non-superuser token."""
    token_data = {
        "sub": TEST_USERNAME,
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    assert is_superuser(token) is False

def test_is_superuser_invalid_token():
    """Test superuser check with invalid token."""
    assert is_superuser("invalid_token") is False