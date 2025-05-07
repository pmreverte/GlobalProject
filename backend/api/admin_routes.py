"""
Administrative API Routes Module

This module provides API endpoints for system administration, including:
- User management
- LLM configuration
- Document processing settings
- SQL server configuration
- System logs and feedback

All routes require superuser privileges and implement role-based access control.
The module provides a comprehensive interface for managing system settings
and monitoring system usage.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.auth.models import (
    User, DocumentConfig, SQLConfig, LLMConfig,
    DocumentRecord, DocumentLog
)
from backend.auth.dependencies import get_user, require_role
from backend.logs.logger import (
    RegistroConsulta,
    FeedbackRespuesta,
    RegistroAdmin,
    registrar_accion_admin
)
from datetime import datetime, timedelta
from sqlalchemy import create_engine, desc
import os
import json
from typing import Dict

# Initialize router with prefix and tag
router = APIRouter(prefix="/admin", tags=["Administración"])

@router.get("/config")
def get_config(current_user=Depends(require_role("superuser"))):
    """
    Verify admin access.
    
    Returns:
        dict: Confirmation message
    """
    return {"message": "Acceso concedido a configuración avanzada"}

@router.get("/llm/config")
def get_llm_configs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Get all active LLM configurations.
    
    Returns:
        List[LLMConfig]: List of active LLM configurations
    """
    configs = db.query(LLMConfig).all()
    return configs

@router.post("/llm/config")
def create_llm_config(
    config: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Create new LLM configuration.
    
    Args:
        config (dict): LLM configuration parameters
        
    Returns:
        LLMConfig: Created configuration
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        # If this config is default, deactivate other defaults
        if config.get('is_default'):
            db.query(LLMConfig).filter(
                LLMConfig.is_default == True
            ).update({'is_default': False})
        
        new_config = LLMConfig(**config)
        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="create",
            modulo="llm_config",
            detalles={"config": config}
        )

        return new_config
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear configuración LLM: {str(e)}"
        )

@router.put("/llm/config/{config_id}")
def update_llm_config(
    config_id: int,
    config: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Update existing LLM configuration.
    
    Args:
        config_id (int): Configuration ID to update
        config (dict): Updated configuration parameters
        
    Returns:
        LLMConfig: Updated configuration
        
    Raises:
        HTTPException: If update fails or config not found
    """
    try:
        existing_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not existing_config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        # If this config will be default, deactivate other defaults
        if config.get('is_default'):
            db.query(LLMConfig).filter(
                LLMConfig.id != config_id,
                LLMConfig.is_default == True
            ).update({'is_default': False})
        
        for key, value in config.items():
            setattr(existing_config, key, value)
        
        db.commit()
        db.refresh(existing_config)

        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="update",
            modulo="llm_config",
            detalles={"config_id": config_id, "changes": config}
        )

        return existing_config
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar configuración LLM: {str(e)}"
        )

@router.delete("/llm/config/{config_id}")
def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Delete LLM configuration.
    
    Args:
        config_id (int): Configuration ID to delete
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If deletion fails or config not found
    """
    try:
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        db.delete(config)
        db.commit()

        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="delete",
            modulo="llm_config",
            detalles={"config_id": config_id}
        )

        return {"message": "Configuración eliminada exitosamente"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar configuración LLM: {str(e)}"
        )

@router.get("/document-config")
def get_document_config(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Get document processing configuration.
    
    Returns:
        DocumentConfig: Current document configuration or None
    """
    config = db.query(DocumentConfig).first()
    if not config:
        return None
    return config

@router.post("/document-config")
def create_document_config(
    config: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Create document processing configuration.
    
    Args:
        config (dict): Configuration parameters
        
    Returns:
        DocumentConfig: Created configuration
        
    Raises:
        HTTPException: If configuration already exists
    """
    existing_config = db.query(DocumentConfig).first()
    if existing_config:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una configuración. Use PUT para actualizarla."
        )
    
    new_config = DocumentConfig(**config)
    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    # Log the action
    registrar_accion_admin(
        usuario=current_user.username,
        accion="create",
        modulo="document_config",
        detalles={"config": config}
    )

    return new_config

@router.put("/document-config")
def update_document_config(
    config: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Update document processing configuration.
    
    Args:
        config (dict): Updated configuration parameters
        
    Returns:
        DocumentConfig: Updated configuration
        
    Raises:
        HTTPException: If configuration doesn't exist
    """
    existing_config = db.query(DocumentConfig).first()
    if not existing_config:
        raise HTTPException(
            status_code=404,
            detail="No existe configuración. Use POST para crear una nueva."
        )
    
    # Remove datetime fields from the update
    config.pop('created_at', None)
    config.pop('updated_at', None)
    
    for key, value in config.items():
        setattr(existing_config, key, value)
    
    db.commit()
    db.refresh(existing_config)

    # Log the action
    registrar_accion_admin(
        usuario=current_user.username,
        accion="update",
        modulo="document_config",
        detalles={"changes": config}
    )

    return existing_config

@router.get("/sql-config")
def get_sql_config(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Get SQL server configurations.
    
    Returns:
        dict: List of SQL server configurations and currently active config
    """
    configs = db.query(SQLConfig).all()
    return {
        "configs": [{
            "id": config.id,
            "server": config.server,
            "database": config.database,
            "username": config.username,
            "driver": config.driver,
            "use_windows_auth": config.use_windows_auth,
            "is_active": config.is_active
        } for config in configs]
    }

@router.post("/sql-config")
def update_sql_config(
    config_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Create or update SQL server configuration.
    
    Args:
        config_data (Dict): SQL server configuration parameters
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If configuration update fails
    """
    # If updating existing config
    if config_data.get('id'):
        config = db.query(SQLConfig).filter(SQLConfig.id == config_data['id']).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        # Update existing configuration
        for key, value in config_data.items():
            if key != 'id':  # Skip updating ID
                setattr(config, key, value)
    else:
        # Create new configuration
        config = SQLConfig(**config_data)
        db.add(config)
    
    # Set this config as active and deactivate others
    db.query(SQLConfig).filter(SQLConfig.id != config.id).update({"is_active": False})
    config.is_active = True
    
    try:
        # Save to database without changing active status
        db.commit()
        db.refresh(config)
        
        # Return the config ID for new configurations
        result = {
            "message": "Configuración guardada exitosamente",
            "id": config.id
        }

        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="update" if config_data.get('id') else "create",
            modulo="sql_config",
            detalles={
                "server": config.server,
                "database": config.database,
                "username": config.username,
                "driver": config.driver,
                "use_windows_auth": config.use_windows_auth
            }
        )
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la configuración: {str(e)}"
        )

@router.delete("/sql-config/{config_id}")
def delete_sql_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Delete SQL server configuration.
    
    Args:
        config_id (int): Configuration ID to delete
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If configuration not found
    """
    try:
        config = db.query(SQLConfig).filter(SQLConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        # If this was the active config, clear sql_config.json
        if config.is_active:
            with open("config/sql_config.json", "w") as f:
                json.dump({
                    "server": "",
                    "database": "",
                    "username": "",
                    "password": "",
                    "driver": "ODBC Driver 17 for SQL Server",
                    "use_windows_auth": False
                }, f, indent=2)
        
        db.delete(config)
        db.commit()
        
        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="delete",
            modulo="sql_config",
            detalles={"config_id": config_id}
        )
        
        return {"message": "Configuración eliminada exitosamente"}
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la configuración: {str(e)}"
        )

@router.post("/sql-config/test")
def test_sql_connection(
    config_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Test SQL server connection with provided configuration.
    
    Args:
        config_data (Dict): SQL server configuration to test
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If connection test fails
    """
    try:
        # Get configuration from database if ID provided
        config = None
        if config_data.get('id'):
            config = db.query(SQLConfig).filter(SQLConfig.id == config_data['id']).first()
            if not config:
                raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        # Parse server name to handle named instances
        server = config_data['server']
        if '\\' in server:
            # For named instances, we need to specify the server in the query parameters
            base_server = server.split('\\')[0]
            instance = server.split('\\')[1]
            if config_data.get('use_windows_auth', False):
                connection_string = f"mssql+pyodbc://{base_server}/{config_data['database']}?driver={config_data['driver'].replace(' ', '+')}&trusted_connection=yes&server={server}"
            else:
                connection_string = f"mssql+pyodbc://{config_data['username']}:{config_data['password']}@{base_server}/{config_data['database']}?driver={config_data['driver'].replace(' ', '+')}&server={server}"
        else:
            # For default instance
            if config_data.get('use_windows_auth', False):
                connection_string = f"mssql+pyodbc://{server}/{config_data['database']}?driver={config_data['driver'].replace(' ', '+')}&trusted_connection=yes"
            else:
                connection_string = f"mssql+pyodbc://{config_data['username']}:{config_data['password']}@{server}/{config_data['database']}?driver={config_data['driver'].replace(' ', '+')}"
        
        # Test connection with timeout
        engine = create_engine(connection_string, connect_args={'timeout': 3})
        
        # Save config temporarily for testing
        with open("config/sql_config.json", "w") as f:
            json.dump({
                "server": config_data['server'],
                "database": config_data['database'],
                "username": config_data.get('username', ''),
                "password": config_data.get('password', ''),
                "driver": config_data['driver'],
                "use_windows_auth": config_data.get('use_windows_auth', False)
            }, f, indent=2)

        # Test connection using the new test function
        from backend.sql.sql_connector import test_connection
        test_result = test_connection()
        
        if not test_result['success']:
            raise Exception(test_result['error'])

        # If test successful and we have a config, set it as active
        if config:
            # Deactivate all other configs
            db.query(SQLConfig).filter(SQLConfig.id != config.id).update({"is_active": False})
            config.is_active = True
            db.commit()
            
            # Update environment variable
            os.environ["SQL_SERVER_URL"] = connection_string

        return {"message": f"Conexión exitosa - {test_result.get('version', '')}"}

        # Log the action
        registrar_accion_admin(
            usuario=current_user.username,
            accion="test",
            modulo="sql_config",
            detalles={
                "server": config_data['server'],
                "database": config_data['database'],
                "username": config_data.get('username'),
                "driver": config_data['driver'],
                "use_windows_auth": config_data.get('use_windows_auth', False),
                "result": "success"
            }
        )
        
        return {"message": "Conexión exitosa"}
    except Exception as e:
        # Log the failed attempt
        registrar_accion_admin(
            usuario=current_user.username,
            accion="test",
            modulo="sql_config",
            detalles={
                "server": config_data['server'],
                "database": config_data['database'],
                "username": config_data.get('username'),
                "driver": config_data['driver'],
                "use_windows_auth": config_data.get('use_windows_auth', False),
                "result": "error",
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al conectar con SQL Server: {str(e)}"
        )

@router.post("/users")
def create_user(
    username: str = Body(default=...),
    full_name: str = Body(default=...),
    password: str = Body(default=...),
    role: str = Body("user"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Create new user.
    
    Args:
        username (str): Username
        full_name (str): User's full name
        password (str): User's password
        role (str): User's role (defaults to "user")
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user already exists
    """
    if get_user(username, db):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    nuevo_usuario = User(
        username=username,
        full_name=full_name,
        role=role.lower()
    )
    nuevo_usuario.set_password(password)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Log the action
    registrar_accion_admin(
        usuario=current_user.username,
        accion="create",
        modulo="users",
        detalles={
            "username": username,
            "full_name": full_name,
            "role": role.lower()
        }
    )

    return {"message": f"Usuario '{username}' creado con éxito"}

@router.put("/users/{username}")
def update_user(
    username: str,
    full_name: str = Body(None),
    password: str = Body(None),
    role: str = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Update existing user.
    
    Args:
        username (str): Username to update
        full_name (str, optional): New full name
        password (str, optional): New password
        role (str, optional): New role
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found
    """
    usuario = get_user(username, db)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    changes = {}
    if full_name:
        usuario.full_name = full_name
        changes["full_name"] = full_name
    if password:
        usuario.set_password(password)
        changes["password"] = "updated"
    if role:
        usuario.role = role.lower()
        changes["role"] = role.lower()

    db.commit()
    db.refresh(usuario)

    # Log the action
    registrar_accion_admin(
        usuario=current_user.username,
        accion="update",
        modulo="users",
        detalles={
            "username": username,
            "changes": changes
        }
    )

    return {"message": f"Usuario '{username}' actualizado"}

@router.delete("/users/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser"))
):
    """
    Delete user.
    
    Args:
        username (str): Username to delete
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found
    """
    usuario = get_user(username, db)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()

    # Log the action
    registrar_accion_admin(
        usuario=current_user.username,
        accion="delete",
        modulo="users",
        detalles={"username": username}
    )

    return {"message": f"Usuario '{username}' eliminado con éxito"}

@router.get("/logs")
def obtener_logs(db: Session = Depends(get_db), current_user=Depends(require_role("superuser"))):
    """
    Get system logs.
    
    Returns:
        List[dict]: List of system logs with query details and admin actions
    """
    # Get query logs
    query_logs = db.query(RegistroConsulta).order_by(desc(RegistroConsulta.fecha)).all()
    
    # Get admin logs
    admin_logs = db.query(RegistroAdmin).order_by(desc(RegistroAdmin.fecha)).all()
    
    # Combine and format logs
    logs = []
    
    # Format query logs
    for log in query_logs:
        logs.append({
            "tipo": "consulta",
            "usuario": log.usuario,
            "pregunta": log.pregunta,
            "sql": log.sql,
            "respuesta": log.respuesta,
            "fecha": log.fecha.isoformat()
        })
    
    # Format admin logs
    for log in admin_logs:
        logs.append({
            "tipo": "admin",
            "usuario": log.usuario,
            "accion": log.accion,
            "modulo": log.modulo,
            "detalles": log.detalles,
            "fecha": log.fecha.isoformat()
        })
    
    # Sort all logs by date, most recent first
    logs.sort(key=lambda x: x["fecha"], reverse=True)
    
    return logs

@router.get("/feedback")
def obtener_feedback(db: Session = Depends(get_db), current_user=Depends(require_role("superuser"))):
    """
    Get user feedback.
    
    Returns:
        List[dict]: List of user feedback entries
    """
    feedbacks = db.query(FeedbackRespuesta).order_by(FeedbackRespuesta.fecha.desc()).all()
    return [
        {
            "usuario": f.usuario,
            "pregunta": f.pregunta,
            "fue_util": f.fue_util,
            "fecha": f.fecha.isoformat()
        } for f in feedbacks
    ]

@router.get("/llm/count")
def get_llm_count(db: Session = Depends(get_db), current_user=Depends(require_role("superuser"))):
    """
    Get count of active LLM configurations.
    
    Returns:
        dict: Count of active configurations
    """
    try:
        count = db.query(LLMConfig).filter(LLMConfig.is_active == True).count()
        return {"count": count}
    except Exception as e:
        print(f"Error getting LLM count: {str(e)}")
        return {"count": 0}

@router.get("/users")
def get_users(db: Session = Depends(get_db), current_user=Depends(require_role("superuser"))):
    """
    Get all users.
    
    Returns:
        List[dict]: List of all users with their details
    """
    users = db.query(User).all()
    return [
        {
            "username": user.username,
            "full_name": user.full_name or "",
            "role": user.role,
            "is_active": user.is_active
        } for user in users
    ]

@router.get("/documents")
def get_document_records(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser")),
    days: int = None
):
    """
    Get document records with optional date filter.
    
    Args:
        days (int, optional): Number of days to look back
        
    Returns:
        List[dict]: List of document records with their details
    """
    query = db.query(DocumentRecord)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(DocumentRecord.upload_date >= cutoff_date)
    
    records = query.order_by(DocumentRecord.upload_date.desc()).all()
    
    return [
        {
            "id": record.id,
            "filename": record.filename,
            "file_path": record.file_path,
            "file_size": record.file_size,
            "file_type": record.file_type,
            "upload_date": record.upload_date.isoformat(),
            "last_modified": record.last_modified.isoformat(),
            "is_indexed": record.is_indexed,
            "is_deleted": record.is_deleted,
            "uploaded_by": record.uploaded_by,
            "user": record.user.username if record.user else None
        } for record in records
    ]

@router.get("/documents/logs")
def get_document_logs(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superuser")),
    days: int = None,
    document_id: int = None
):
    """
    Get document activity logs with optional filters.
    
    Args:
        days (int, optional): Number of days to look back
        document_id (int, optional): Filter logs for specific document
        
    Returns:
        List[dict]: List of document activity logs
    """
    query = db.query(DocumentLog)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(DocumentLog.timestamp >= cutoff_date)
    
    if document_id:
        query = query.filter(DocumentLog.document_id == document_id)
    
    logs = query.order_by(DocumentLog.timestamp.desc()).all()
    
    return [
        {
            "id": log.id,
            "document_id": log.document_id,
            "document": log.document.filename if log.document else None,
            "user_id": log.user_id,
            "user": log.user.username if log.user else None,
            "action": log.action,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details
        } for log in logs
    ]
