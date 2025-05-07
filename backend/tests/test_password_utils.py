"""
Unit tests for the password utilities module.
"""

import pytest
from backend.auth.password_utils import get_password_hash, verify_password

def test_password_hash_not_plain_text():
    """Test that the hashed password is not the same as the plain text password."""
    password = "mypassword123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert len(hashed) > len(password)
    assert hashed.startswith("$2b$")  # bcrypt identifier

def test_password_hash_uniqueness():
    """Test that the same password generates different hashes (due to salt)."""
    password = "mypassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    assert hash1 != hash2

def test_verify_password_success():
    """Test successful password verification."""
    password = "mypassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True

def test_verify_password_failure():
    """Test failed password verification with wrong password."""
    password = "mypassword123"
    wrong_password = "wrongpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(wrong_password, hashed) is False

def test_verify_password_empty():
    """Test password verification with empty strings."""
    password = ""
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("somepassword", hashed) is False

def test_verify_password_special_chars():
    """Test password verification with special characters."""
    password = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True

def test_verify_password_unicode():
    """Test password verification with unicode characters."""
    password = "contraseña123アイウエオ"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True

def test_hash_length_consistency():
    """Test that generated hashes have consistent length."""
    passwords = [
        "short",
        "mediumpassword",
        "averylongpasswordstring",
        "!@#$%^&*()",
        "contraseña123"
    ]
    
    # Get the lengths of all hashes
    hash_lengths = [len(get_password_hash(p)) for p in passwords]
    
    # All bcrypt hashes should have the same length
    assert all(length == hash_lengths[0] for length in hash_lengths)

def test_verify_password_case_sensitive():
    """Test that password verification is case sensitive."""
    password = "MyPassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password(password.lower(), hashed) is False
    assert verify_password(password.upper(), hashed) is False

def test_verify_password_with_spaces():
    """Test password verification with leading/trailing spaces."""
    password = "  password with spaces  "
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password(password.strip(), hashed) is False

def test_long_password():
    """Test handling of very long passwords."""
    # Test with a reasonably long password instead of relying on bcrypt truncation
    password = "a" * 100
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True
    # Test that a different long password doesn't verify
    assert verify_password("b" * 100, hashed) is False