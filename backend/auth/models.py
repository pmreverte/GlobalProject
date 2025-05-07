"""
Database Models Module

This module defines the SQLAlchemy ORM models for the application's database schema.
It includes models for users, LLM configurations, document handling settings, and SQL server connections.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.db.database import Base
from datetime import datetime

from backend.auth.password_utils import get_password_hash

class User(Base):
    """
    User Model
    
    Represents a user in the system with authentication and authorization details.
    
    Attributes:
        id (int): Primary key
        username (str): Unique username for identification
        full_name (str): User's full name
        hashed_password (str): Securely hashed password
        role (str): User's role for authorization (e.g., "admin", "user")
        is_active (bool): Whether the user account is active
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    role = Column(String(50))
    is_active = Column(Boolean, default=True)

    def set_password(self, password: str):
        """
        Set a new password for the user.
        
        Args:
            password (str): Plain text password to be hashed
        """
        self.hashed_password = get_password_hash(password)

class LLMConfig(Base):
    """
    Language Model Configuration
    
    Stores configuration settings for different language models used in the application.
    
    Attributes:
        id (int): Primary key
        name (str): Unique name for the configuration
        provider (str): LLM provider (e.g., "openai", "anthropic")
        model_name (str): Specific model identifier
        api_key (str): API key for authentication with the provider
        temperature (str): Model temperature setting for response randomness
        is_active (bool): Whether this configuration is active
        is_default (bool): Whether this is the default configuration
    """
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    provider = Column(String(50))  # e.g., "openai", "anthropic", etc.
    model_name = Column(String(100))  # e.g., "gpt-4", "gpt-3.5-turbo"
    api_key = Column(String(255))
    temperature = Column(String(10))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

class DocumentConfig(Base):
    """
    Document Configuration
    
    Manages settings for document handling and storage in the application.
    
    Attributes:
        id (int): Primary key
        max_file_size (int): Maximum allowed file size in MB
        allowed_extensions (str): Comma-separated list of allowed file extensions
        max_files_per_upload (int): Maximum number of files per upload
        storage_path (str): Path where uploaded files are stored
        is_active (bool): Whether this configuration is active
        created_at (datetime): Timestamp of creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = "document_configs"

    id = Column(Integer, primary_key=True, index=True)
    max_file_size = Column(Integer, default=10)  # in MB
    allowed_extensions = Column(String(255), default=".pdf,.doc,.docx,.txt")
    max_files_per_upload = Column(Integer, default=5)
    storage_path = Column(String(255), default="uploads/")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class SQLConfig(Base):
    """
    SQL Server Configuration
    
    Stores connection settings for SQL Server databases.
    
    Attributes:
        id (int): Primary key
        server (str): SQL Server hostname or IP address
        database (str): Database name
        username (str): SQL Server authentication username (optional for Windows auth)
        password (str): SQL Server authentication password (optional for Windows auth)
        driver (str): SQL Server driver name
        use_windows_auth (bool): Whether to use Windows authentication
        is_active (bool): Whether this configuration is active
        created_at (datetime): Timestamp of creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = "sql_configs"

    id = Column(Integer, primary_key=True, index=True)
    server = Column(String(255), nullable=False)
    database = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)  # Nullable para autenticación de Windows
    password = Column(String(255), nullable=True)  # Nullable para autenticación de Windows
    driver = Column(String(255), default="ODBC Driver 17 for SQL Server")
    use_windows_auth = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class DocumentRecord(Base):
    """
    Document Record
    
    Tracks uploaded documents and their current status in the system.
    
    Attributes:
        id (int): Primary key
        filename (str): Original filename
        file_path (str): Path where the file is stored
        file_size (int): Size of file in bytes
        file_type (str): File extension/type
        upload_date (datetime): When the file was uploaded
        last_modified (datetime): Last modification timestamp
        is_indexed (bool): Whether the file is indexed in vector store
        is_deleted (bool): Soft delete flag
        uploaded_by (int): Foreign key to users table
        user (User): Relationship to user who uploaded
    """
    __tablename__ = "document_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)
    file_path = Column(String(500))
    file_size = Column(Integer)  # in bytes
    file_type = Column(String(50))
    upload_date = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow)
    is_indexed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

class DocumentLog(Base):
    """
    Document Activity Log
    
    Records all actions performed on documents for auditing.
    
    Attributes:
        id (int): Primary key
        document_id (int): Foreign key to document_records
        user_id (int): Foreign key to users table
        action (str): Type of action performed (upload, delete, update, index)
        timestamp (datetime): When the action occurred
        details (str): Additional information about the action
        document (DocumentRecord): Relationship to affected document
        user (User): Relationship to user who performed action
    """
    __tablename__ = "document_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document_records.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))  # upload, delete, update, index
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String(500))
    
    document = relationship("DocumentRecord")
    user = relationship("User")
