"""
Admin User Creation Script

This script provides functionality to create a superuser (admin) account in the system.
It's typically used during initial system setup or when a new admin account is needed.

The script:
1. Sets up the database connection
2. Creates a new user with superuser privileges
3. Securely hashes the provided password
4. Handles any errors during the creation process

Usage:
    python create_admin_user.py

Environment Variables:
    DATABASE_URL: Database connection string (from .env file)
    Other database-related environment variables as needed
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.auth.models import User

def create_admin_user(username: str, password: str, full_name: str = "Administrador"):
    """
    Create a new administrator user in the system.
    
    This function creates a new user with superuser privileges. It handles:
    - Password hashing
    - Database transaction management
    - Error handling and rollback
    
    Args:
        username (str): Login username for the admin user
        password (str): Plain text password (will be hashed)
        full_name (str, optional): Full name of the admin user. Defaults to "Administrador"
        
    Note:
        The function uses a database transaction to ensure data consistency.
        If any error occurs during the process, the transaction is rolled back.
        
    Example:
        create_admin_user("admin", "secure_password", "System Administrator")
    """
    # Create new database session
    db: Session = SessionLocal()
    try:
        # Create new user with administrator role
        admin_user = User(
            username=username,
            full_name=full_name,
            role="superuser".lower(),  # Ensure consistent case
            is_active=True
        )
        # Hash and set the password
        admin_user.set_password(password)
        
        # Add user to session and commit transaction
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Usuario administrador '{username}' creado con éxito.")
    except Exception as e:
        # Rollback transaction on error
        db.rollback()
        print(f"Error al crear el usuario administrador: {e}")
    finally:
        # Always close the database session
        db.close()

# Example usage when script is run directly
if __name__ == "__main__":
    # Create default admin user
    # In production, you should use more secure credentials
    create_admin_user("admin", "adminpassword", "Administrador del Sistema")