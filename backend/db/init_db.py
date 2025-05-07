"""
Database Initialization Script

This script handles the initialization and reset of the application's database schema.
It manages multiple database models across different modules:
- Authentication models (users, roles)
- Analytics models (usage statistics)
- Logging models (system logs)

The script performs a complete reset of the database by:
1. Dropping all existing tables
2. Creating fresh tables based on SQLAlchemy models
3. Setting up initial schema

Usage:
    python init_db.py

Environment Variables:
    DATABASE_URL: Database connection string (from .env file)
    Other database-related environment variables as needed

Warning:
    This script will DELETE ALL DATA in the specified tables.
    Use with caution, especially in production environments.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables before any database operations
load_dotenv()

# Add the project root to Python path for proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import database components after environment is configured
from backend.db.database import engine
from backend.auth.models import Base as AuthBase
from backend.models.analytics import Base as AnalyticsBase
from backend.logs.logger import Base as LogsBase

def init_db():
    """
    Initialize the database by recreating all tables.
    
    This function:
    1. Drops all existing tables in the database
    2. Creates new tables based on SQLAlchemy models
    3. Handles different model bases from various modules:
       - AuthBase: Authentication-related tables
       - AnalyticsBase: Analytics and statistics tables
       - LogsBase: System logging tables
    
    The function uses SQLAlchemy's metadata management to:
    - Ensure proper table dependencies
    - Handle foreign key relationships
    - Maintain schema consistency
    
    Raises:
        Exception: If there's an error during table management
        
    Note:
        This operation is destructive and will erase all existing data.
        Make sure to backup any important data before running this function.
    """
    try:
        # Drop all existing tables
        # This ensures a clean slate for the new schema
        AuthBase.metadata.drop_all(bind=engine)
        AnalyticsBase.metadata.drop_all(bind=engine)
        LogsBase.metadata.drop_all(bind=engine)
        print("Existing tables dropped successfully!")
        
        # Create all tables based on current models
        # Tables are created in the correct order to handle dependencies
        AuthBase.metadata.create_all(bind=engine)
        AnalyticsBase.metadata.create_all(bind=engine)
        LogsBase.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error managing database tables: {e}")

if __name__ == "__main__":
    # Ensure environment variables are loaded when run directly
    load_dotenv()
    init_db()