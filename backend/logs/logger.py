"""
Logging System Module

This module implements a comprehensive logging system for tracking queries,
responses, and user feedback. It provides:
- Query logging with detailed execution information
- Error tracking with stack traces
- User feedback collection
- Performance monitoring
- Administrative action logging

The module uses SQLAlchemy models to store logs in the database,
enabling detailed analysis and monitoring of system usage and performance.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Session
from datetime import datetime
import traceback
import json
from backend.db.database import Base, SessionLocal

class RegistroConsulta(Base):
    """
    Query Log Model
    
    Tracks detailed information about each query execution including
    the input, output, and any errors that occurred.
    
    Attributes:
        id (int): Primary key
        usuario (str): Username who made the query
        pregunta (Text): Original question/query text
        sql (Text): Generated SQL query
        resultado (Text): Query execution result
        respuesta (Text): Final response provided to user
        llm_id (int): ID of LLM configuration used
        fecha (datetime): Timestamp of the query
        error_details (JSON): Structured error information if any
        stack_trace (Text): Full stack trace if error occurred
        
    Note:
        The model captures both successful queries and failures,
        providing comprehensive debugging information when needed.
    """
    __tablename__ = "logs_consultas"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100), index=True)
    pregunta = Column(Text)
    sql = Column(Text)
    resultado = Column(Text)
    respuesta = Column(Text)
    llm_id = Column(Integer, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    error_details = Column(JSON, nullable=True)
    stack_trace = Column(Text, nullable=True)

class FeedbackRespuesta(Base):
    """
    Response Feedback Model
    
    Stores user feedback about query responses for quality monitoring
    and system improvement.
    
    Attributes:
        id (int): Primary key
        usuario (str): Username who provided feedback
        pregunta (Text): Original question text
        fue_util (bool): Whether the response was helpful
        llm_id (int): ID of LLM configuration used
        fecha (datetime): Timestamp of feedback submission
        
    Note:
        This feedback helps in:
        - Monitoring response quality
        - Identifying areas for improvement
        - Training and fine-tuning models
    """
    __tablename__ = "feedback_respuestas"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100), index=True)
    pregunta = Column(Text)
    fue_util = Column(Boolean)
    llm_id = Column(Integer, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

class RegistroAdmin(Base):
    """
    Administrative Action Log Model
    
    Tracks all administrative actions performed in the system.
    
    Attributes:
        id (int): Primary key
        usuario (str): Username of the admin who performed the action
        accion (str): Type of action performed (create, update, delete)
        modulo (str): Module where the action was performed (users, llm, docs, etc.)
        detalles (JSON): Details of the action performed
        fecha (datetime): Timestamp of the action
    """
    __tablename__ = "logs_admin"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100), index=True)
    accion = Column(String(50))
    modulo = Column(String(50))
    detalles = Column(JSON)
    fecha = Column(DateTime, default=datetime.utcnow)

def registrar_consulta(
    usuario: str,
    pregunta: str,
    sql: str,
    resultado: dict,
    respuesta: str,
    llm_id: int = None,
    error_details: dict = None
):
    """
    Log a query execution with all its details.
    
    This function creates a comprehensive log entry for a query execution,
    including any errors that occurred during processing.
    
    Args:
        usuario (str): Username who made the query
        pregunta (str): Original question text
        sql (str): Generated SQL query
        resultado (dict): Query execution result
        respuesta (str): Final response provided
        llm_id (int, optional): LLM configuration ID used
        error_details (dict, optional): Error information if any
        
    Raises:
        Exception: If there's an error during log creation
        
    Note:
        - Automatically captures stack traces for errors
        - Converts complex result objects to JSON
        - Handles transaction management
    """
    db: Session = SessionLocal()
    try:
        # Capture stack trace if error occurred
        stack_trace = None
        if error_details:
            stack_trace = traceback.format_stack()
            
        # Convert result to JSON string if possible
        resultado_str = (
            json.dumps(resultado)
            if isinstance(resultado, dict)
            else str(resultado)
        )
        
        log = RegistroConsulta(
            usuario=usuario,
            pregunta=pregunta,
            sql=sql,
            resultado=resultado_str,
            respuesta=respuesta,
            llm_id=llm_id,
            error_details=error_details,
            stack_trace='\n'.join(stack_trace) if stack_trace else None
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Error al registrar consulta: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def registrar_feedback(usuario: str, pregunta: str, fue_util: bool, llm_id: int = None):
    """
    Record user feedback about a query response.
    
    This function stores user feedback about whether a response was helpful,
    which is valuable for quality monitoring and improvement.
    
    Args:
        usuario (str): Username who provided feedback
        pregunta (str): Original question text
        fue_util (bool): Whether the response was helpful
        llm_id (int, optional): LLM configuration ID used
        
    Note:
        This feedback is crucial for:
        - Monitoring system effectiveness
        - Identifying patterns in unhelpful responses
        - Guiding system improvements
    """
    db: Session = SessionLocal()
    try:
        feedback = FeedbackRespuesta(
            usuario=usuario,
            pregunta=pregunta,
            fue_util=fue_util,
            llm_id=llm_id
        )
        db.add(feedback)
        db.commit()
    finally:
        db.close()

def registrar_accion_admin(usuario: str, accion: str, modulo: str, detalles: dict):
    """
    Record an administrative action.
    
    This function logs all administrative actions performed in the system,
    providing an audit trail of system changes.
    
    Args:
        usuario (str): Username of the admin who performed the action
        accion (str): Type of action performed (create, update, delete)
        modulo (str): Module where the action was performed
        detalles (dict): Details of the action performed
    """
    db: Session = SessionLocal()
    try:
        log = RegistroAdmin(
            usuario=usuario,
            accion=accion,
            modulo=modulo,
            detalles=detalles
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Error al registrar acción admin: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
