"""
Authentication System Module

This module implements a JWT-based authentication system for the application.
It provides functionality for user authentication, token generation, and validation.

Key components:
- Token generation and validation
- User authentication
- Role-based access control
- Protected route handlers
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import os
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.auth.models import User as DBUser
from backend.auth.password_utils import verify_password

# Configuration constants
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "defaultsecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class Token(BaseModel):
    """
    Token response model.
    
    Attributes:
        access_token (str): The JWT access token
        token_type (str): The type of token (always "bearer")
    """
    access_token: str
    token_type: str

class UserBase(BaseModel):
    """
    Base user model for responses.
    
    Attributes:
        username (str): The user's username
        role (str): The user's role in the system
    """
    username: str
    role: str

    class Config:
        from_attributes = True

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
router = APIRouter(prefix="/auth", tags=["Autenticación"])

def get_user(username: str, db: Session) -> DBUser:
    """
    Retrieve a user from the database by username.
    
    Args:
        username (str): The username to search for
        db (Session): Database session
        
    Returns:
        DBUser: The user object if found, None otherwise
    """
    return db.query(DBUser).filter(DBUser.username == username).first()

def authenticate_user(username: str, password: str, db: Session) -> DBUser:
    """
    Authenticate a user with username and password.
    
    Args:
        username (str): The username to authenticate
        password (str): The password to verify
        db (Session): Database session
        
    Returns:
        DBUser: The authenticated user object if successful, None otherwise
    """
    user = get_user(username, db)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data (dict): The data to encode in the token
        expires_delta (timedelta, optional): Token expiration time
        
    Returns:
        str: The encoded JWT token
        
    Raises:
        ValueError: If required claims are missing
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access_token"
    })
    
    if "sub" not in to_encode or "role" not in to_encode:
        raise ValueError("El token debe contener 'sub' y 'role'")
        
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def is_superuser(token: str) -> bool:
    """
    Check if a token belongs to a superuser.
    
    Args:
        token (str): The JWT token to check
        
    Returns:
        bool: True if the token belongs to a superuser, False otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role") == "superuser"
    except JWTError:
        return False

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and create access token.
    
    Args:
        form_data (OAuth2PasswordRequestForm): The login credentials
        db (Session): Database session
        
    Returns:
        dict: Token response containing access_token and token_type
        
    Raises:
        HTTPException: If authentication fails or user is inactive
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        access_token = create_access_token(
            data={
                "sub": user.username,
                "role": user.role
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el token: {str(e)}"
        )

@router.get("/me", response_model=UserBase)
async def read_users_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get current authenticated user information.
    
    Args:
        token (str): JWT token from request
        db (Session): Database session
        
    Returns:
        UserBase: Current user information
        
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        role: str = payload.get("role")
        
        if not username or not role:
            raise HTTPException(
                status_code=401,
                detail="Token malformado: falta información requerida",
                headers={"WWW-Authenticate": "Bearer"}
            )

        exp = payload.get("exp")
        if exp:
            current_time = datetime.now(timezone.utc).timestamp()
            if current_time > exp:
                raise HTTPException(
                    status_code=401,
                    detail="Token expirado",
                    headers={"WWW-Authenticate": "Bearer"}
                )

        user = get_user(username, db)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Usuario inactivo",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if user.role.lower() != role.lower():
            raise HTTPException(
                status_code=401,
                detail="Información de rol inválida",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user
        
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )
