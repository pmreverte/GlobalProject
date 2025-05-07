"""
User API Routes Module

This module provides endpoints for user-specific operations.
It handles user profile access and management, implementing
role-based access control to ensure proper authorization.

Features:
- User profile access
- Role-based authorization
- User data management
"""

from fastapi import APIRouter, Depends
from backend.auth.dependencies import require_role

# Initialize router with prefix and tag
router = APIRouter(prefix="/user", tags=["Usuario"])

@router.get("/perfil")
def get_user_profile(current_user=Depends(require_role("user"))):
    """
    Get current user's profile information.
    
    This endpoint requires user role authentication and provides
    access to standard user data.
    
    Args:
        current_user: User object from role-based dependency
        
    Returns:
        dict: User profile access confirmation
        
    Note:
        This endpoint demonstrates role-based access control
        where only authenticated users can access their profile data.
    """
    return {"message": "Acceso a datos de usuario estándar"}
