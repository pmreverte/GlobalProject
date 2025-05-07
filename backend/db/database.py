"""
Database Configuration Module

This module sets up the SQLAlchemy database connection and session management.
It provides the core database functionality used throughout the application:
- Database engine configuration
- Session management
- Base class for models
- Database connection handling

The module uses environment variables for configuration to maintain security
and flexibility across different deployment environments.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get database URL from environment variables
# This should be defined in the .env file
# Format: "mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"
DATABASE_URL = os.getenv("SQL_SERVER_URL")

# Use SQLite for testing
TESTING = os.getenv("TESTING", "false").lower() == "true"
if TESTING:
    DATABASE_URL = "sqlite:///./test.db"
elif not DATABASE_URL:
    raise ValueError("Database URL not configured. Set SQL_SERVER_URL environment variable.")

# Create SQLAlchemy engine
# The engine is the starting point for any SQLAlchemy application
# It maintains the database connection pool and handles the dialect-specific
# details of talking to the database
connect_args = {"check_same_thread": False} if TESTING else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create session factory
# SessionLocal is used to create database sessions
# - autocommit=False: Transactions must be explicitly committed
# - autoflush=False: Changes won't be automatically flushed to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
# This is the base class from which all mapped classes should inherit
# It provides a consistent interface for model definitions
Base = declarative_base()

def get_db():
    """
    Database session dependency.
    
    This function creates a new SQLAlchemy SessionLocal that will be used in a single request,
    and then closed once the request is finished.
    
    Yields:
        SessionLocal: A SQLAlchemy session instance
        
    Usage:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
            
    Note:
        The function uses a try/finally pattern to ensure the database session is always
        properly closed, even if an exception occurs during the request.
        This prevents resource leaks and connection pool exhaustion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
