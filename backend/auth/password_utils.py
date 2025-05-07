"""
Password Utilities Module

This module provides secure password hashing and verification functionality using the passlib library.
It uses bcrypt as the default hashing algorithm, which is considered cryptographically secure
and includes salt generation and proper work factors for security.

Example:
    hashed = get_password_hash("mypassword123")
    is_valid = verify_password("mypassword123", hashed)  # Returns True
"""

from passlib.context import CryptContext

# Initialize password hashing context with bcrypt
# bcrypt is chosen for its security properties:
# - Includes salt generation
# - Configurable work factor
# - Resistant to rainbow table attacks
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    This function takes a plain text password and returns a secure hash using bcrypt.
    The hash includes the salt and work factor, making it self-contained.

    Args:
        password (str): The plain text password to hash

    Returns:
        str: The complete hash string that can be stored in the database
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    This function safely compares a plain text password against a previously
    generated hash to determine if they match.

    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The previously generated hash to check against

    Returns:
        bool: True if the password matches the hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)