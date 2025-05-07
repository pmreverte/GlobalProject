"""
Analytics Models Module

This module defines the SQLAlchemy ORM models for tracking and analyzing
system usage, including conversations and queries. It provides:
- Conversation tracking
- Query history
- User interaction analytics
- Performance metrics
- Feedback collection

The models support comprehensive analytics and reporting features
while maintaining relationships between users, conversations, and queries.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from backend.db.database import Base
from datetime import datetime

class Conversation(Base):
    """
    Conversation Model
    
    Represents a conversation session between a user and the system.
    Tracks the overall context of multiple related queries.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to users table
        started_at (datetime): Timestamp when conversation started
        is_active (bool): Whether the conversation is ongoing
        
    Relationships:
        user: Reference to the User model
        queries: List of Query objects in this conversation
        
    Note:
        A conversation can contain multiple queries and maintains
        the context across these interactions.
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="conversations")
    queries = relationship("Query", back_populates="conversation")

class Query(Base):
    """
    Query Model
    
    Represents a single query interaction with the system.
    Tracks the details of the query, response, and associated metrics.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to users table
        conversation_id (int): Foreign key to conversations table
        query (Text): The user's original query
        response (Text): System's response to the query
        sql_generado (Text): Generated SQL query if applicable
        feedback (str): User feedback on response quality
            Values: 'positive', 'negative', 'neutral'
        topic (Text): Categorized topic of the query
        response_time (float): Time taken to generate response (seconds)
        llm_id (int): ID of the LLM configuration used
        timestamp (datetime): When the query was made
        
    Relationships:
        user: Reference to the User model
        conversation: Reference to the parent Conversation
        
    Usage:
        This model is crucial for:
        - Performance monitoring
        - Quality assessment
        - Usage patterns analysis
        - System optimization
    """
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    query = Column(Text)
    response = Column(Text)
    sql_generado = Column(Text, nullable=True)
    feedback = Column(String(50))  # positive, negative, neutral
    topic = Column(Text)
    response_time = Column(Float)  # in seconds
    llm_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="queries")
    conversation = relationship("Conversation", back_populates="queries")