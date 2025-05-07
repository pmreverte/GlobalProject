"""
Authentication Dependencies Module

This module provides FastAPI dependency functions for authentication and authorization.
It implements JWT token validation, user authentication, and role-based access control.

The module uses dependency injection to provide:
- Database session management
- Current user extraction from JWT tokens
- Role-based access control for routes
"""

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from backend.db.database import SessionLocal
from backend.auth.models import User
from fastapi.security import OAuth2PasswordBearer
import os

# Configuration constants
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "defaultsecret")
ALGORITHM = "HS256"

# OAuth2 configuration for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    """
    Database session dependency.
    
    Creates a new database session for each request and ensures proper cleanup.
    
    Yields:
        SessionLocal: A SQLAlchemy session instance
        
    Note:
        Uses yield to ensure the session is properly closed after the request,
        even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(username: str, db):
    """
    Retrieve a user from the database.
    
    Args:
        username (str): Username to search for
        db: Database session
        
    Returns:
        User: User instance if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    """
    Dependency to get the current authenticated user from a JWT token.
    
    Args:
        token (str): JWT token from request header
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
        
    Note:
        This dependency is used to protect routes that require authentication.
        It validates the JWT token and ensures the user exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user(username, db)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

def require_role(required_role: str):
    """
    Factory for role-based access control dependencies.
    
    Creates a dependency that checks if the current user has the required role.
    Implements a hierarchical role system where:
    - Superusers have access to everything
    - Users with role "user" or "normal" can access routes requiring "user" role
    - Other roles must match exactly
    
    Args:
        required_role (str): The role required to access the route
        
    Returns:
        callable: A dependency function that validates the user's role
        
    Example:
        @app.get("/admin", dependencies=[Depends(require_role("admin"))])
        def admin_route():
            return {"message": "Admin only"}
            
    Note:
        The role check is case-insensitive for better usability.
    """
    def role_dependency(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Token inválido")
            user = get_user(username, db)
            if user is None:
                raise HTTPException(status_code=403, detail="Usuario no encontrado")
            
            # Access is granted if:
            # - User is superuser (has access to everything)
            # - Required role is "user" and user has role "user" or "normal"
            # - Or if user's role matches exactly with required role
            user_role = user.role.lower()
            if not (
                user_role == "superuser" or
                (required_role.lower() == "user" and user_role in ["user", "normal"]) or
                user_role == required_role.lower()
            ):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")
            
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido")
    return role_dependency
