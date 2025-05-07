"""
Query Processing API Routes Module

This module provides endpoints for:
- Intelligent query processing combining SQL and document sources
- Conversation management
- Document upload and management
- User feedback collection

The module implements a comprehensive query processing system that:
- Maintains conversation context
- Processes queries using multiple data sources
- Handles document uploads and indexing
- Tracks user feedback
"""

from fastapi import APIRouter, Depends, Body, HTTPException, UploadFile, File, Form
from backend.auth.dependencies import require_role
from backend.core.query_router import responder_a_pregunta_combinada
from backend.logs.logger import registrar_consulta, registrar_feedback
from backend.documents.doc_indexer import cargar_y_indexar_documentos, eliminar_documento_indexado
from backend.db.database import get_db
from backend.models.analytics import Query, Conversation
from backend.auth.models import User
from typing import List
from sqlalchemy.orm import Session
import os
import shutil
import json

router = APIRouter(prefix="/query", tags=["Consultas"])

@router.post("/conversacion/nueva")
def nueva_conversacion(
    current_user=Depends(require_role("user")),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation for the user.
    
    This endpoint:
    1. Deactivates any existing active conversations
    2. Creates a new active conversation
    
    Returns:
        dict: New conversation ID
        
    Raises:
        HTTPException: If conversation creation fails
    """
    try:
        # Deactivate previous conversations
        conversaciones_activas = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).all()
        for conv in conversaciones_activas:
            conv.is_active = False
        
        # Create new conversation
        nueva_conv = Conversation(user_id=current_user.id)
        db.add(nueva_conv)
        db.commit()
        
        return {"conversation_id": nueva_conv.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear nueva conversación: {str(e)}"
        )

@router.get("/historial")
def obtener_historial(
    current_user=Depends(require_role("user")),
    db: Session = Depends(get_db)
):
    """
    Get conversation history for current user.
    
    This endpoint:
    1. Retrieves or creates active conversation
    2. Gets all queries in the conversation
    3. Formats conversation history for frontend
    
    Returns:
        dict: Conversation history and ID
        
    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        # Get active conversation
        conversacion_activa = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).first()
        
        if not conversacion_activa:
            # Create new conversation if none active
            conversacion_activa = Conversation(user_id=current_user.id)
            db.add(conversacion_activa)
            db.commit()
        
        # Get all queries in active conversation
        consultas = db.query(Query).filter(
            Query.conversation_id == conversacion_activa.id
        ).order_by(Query.timestamp.asc()).all()
        
        # Format queries for frontend
        historial = []
        for consulta in consultas:
            # Add question
            historial.append({
                "type": "pregunta",
                "content": consulta.query,
                "timestamp": consulta.timestamp.isoformat(),
                "conversation_id": conversacion_activa.id
            })
            # Add response with feedback
            historial.append({
                "type": "respuesta",
                "content": consulta.response,
                "timestamp": consulta.timestamp.isoformat(),
                "conversation_id": conversacion_activa.id,
                "feedback": {"fue_util": consulta.feedback == "positive"} if consulta.feedback in ["positive", "negative"] else None
            })
            
        return {
            "historial": historial,
            "conversation_id": conversacion_activa.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial: {str(e)}"
        )

@router.post("/inteligente")
def consulta_combinada(
    pregunta: str = Body(...),
    llm_id: int | None = Body(None),
    current_user=Depends(require_role("user")),
    db: Session = Depends(get_db)
):
    """
    Process an intelligent query using multiple data sources.
    
    This endpoint:
    1. Gets or creates active conversation
    2. Processes query using SQL and document sources
    3. Records query and response
    4. Handles errors and partial failures
    
    Args:
        pregunta (str): User's question
        llm_id (int, optional): Specific LLM configuration to use
        
    Returns:
        dict: Query results and conversation context
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Get or create active conversation
        conversacion_activa = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).first()
        
        if not conversacion_activa:
            conversacion_activa = Conversation(user_id=current_user.id)
            db.add(conversacion_activa)
            db.commit()

        try:
            resultado = responder_a_pregunta_combinada(pregunta, llm_id)
        except Exception as e:
            error_msg = str(e)
            error_details = {
                "error_type": type(e).__name__,
                "error_message": error_msg,
                "stage": "responder_a_pregunta_combinada"
            }
            
            # Log failed query with error details
            registrar_consulta(
                usuario=current_user.username,
                pregunta=pregunta,
                sql=None,
                resultado={},
                respuesta=f"Error al procesar la consulta: {error_msg}",
                llm_id=llm_id,
                error_details=error_details
            )
            
            # Record in conversations table
            error_topic = json.dumps({"error": error_details})
            nueva_consulta = Query(
                user_id=current_user.id,
                conversation_id=conversacion_activa.id,
                query=pregunta,
                response=f"Error al procesar la consulta: {error_msg}",
                topic=error_topic,
                sql_generado=None,
                llm_id=llm_id
            )
            db.add(nueva_consulta)
            db.commit()
            
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Error al procesar la consulta",
                    "error_details": error_details
                }
            )

        # Create new query associated with conversation
        topic_json = json.dumps(resultado["fuente"])
        nueva_consulta = Query(
            user_id=current_user.id,
            conversation_id=conversacion_activa.id,
            query=resultado["pregunta"],
            response=resultado["respuesta"],
            topic=topic_json,
            sql_generado=resultado["sql_generado"],
            llm_id=llm_id
        )
        db.add(nueva_consulta)
        db.commit()

        response_data = {
            **resultado,
            "conversation_id": conversacion_activa.id
        }
        
        # Include partial errors if any
        if resultado.get("error_details"):
            response_data["warnings"] = resultado["error_details"]

        return response_data

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error inesperado en consulta_combinada: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Error inesperado al procesar la consulta",
                "error": str(e)
            }
        )

@router.post("/documentos/cargar")
def cargar_documento(
    archivos: List[UploadFile] = File(...),
    current_user=Depends(require_role("superuser")),
    db=Depends(get_db)
):
    """
    Upload and process documents.
    
    This endpoint:
    1. Validates uploaded files
    2. Processes valid documents
    3. Indexes documents for search
    
    Args:
        archivos (List[UploadFile]): Files to upload
        
    Returns:
        dict: Processing results and statistics
        
    Raises:
        HTTPException: If file processing fails
    """
    try:
        from backend.documents.doc_indexer import get_document_config, is_valid_file
        config = get_document_config(db)
        temp_dir = "./uploads"
        os.makedirs(temp_dir, exist_ok=True)

        archivos_validos = []
        archivos_invalidos = []

        # Process each file
        for archivo in archivos:
            temp_path = os.path.join(temp_dir, archivo.filename)
            try:
                # Save temporarily for validation
                with open(temp_path, "wb") as f:
                    contenido = archivo.file.read()
                    f.write(contenido)
                
                # Validate file
                if is_valid_file(temp_path, config):
                    archivos_validos.append(archivo.filename)
                    archivo.file.seek(0)  # Reset file pointer
                else:
                    archivos_invalidos.append(archivo.filename)
                    os.remove(temp_path)
            except Exception as e:
                print(f"Error procesando archivo {archivo.filename}: {str(e)}")
                archivos_invalidos.append(archivo.filename)
                continue

        if not archivos_validos:
            return {
                "resultado": "No se encontraron archivos válidos para procesar",
                "archivos_invalidos": archivos_invalidos,
                "extensiones_permitidas": config.allowed_extensions,
                "total_archivos": len(archivos)
            }

        # Process valid files
        mensaje, archivos_procesados = cargar_y_indexar_documentos(temp_dir, current_user.id, recursivo=False, db=db)
        
        return {
            "resultado": mensaje,
            "archivos_procesados": archivos_procesados,
            "archivos_invalidos": archivos_invalidos,
            "total_archivos": len(archivos),
            "archivos_validos": len(archivos_validos),
            "extensiones_permitidas": config.allowed_extensions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar los archivos: {str(e)}"
        )

@router.post("/documentos/cargar-carpeta")
def cargar_carpeta(
    archivos: List[UploadFile] = File(...),
    current_user=Depends(require_role("superuser")),
    db=Depends(get_db)
):
    """
    Upload and process a directory of documents.
    
    This endpoint:
    1. Maintains directory structure
    2. Validates all files
    3. Processes valid documents recursively
    
    Args:
        archivos (List[UploadFile]): Files to upload
        
    Returns:
        dict: Processing results and statistics
        
    Raises:
        HTTPException: If directory processing fails
    """
    try:
        from backend.documents.doc_indexer import get_document_config, is_valid_file
        config = get_document_config(db)
        temp_dir = "./uploads"
        os.makedirs(temp_dir, exist_ok=True)

        archivos_validos = []
        archivos_invalidos = []

        # Process each file
        for archivo in archivos:
            relative_path = archivo.filename
            file_path = os.path.join(temp_dir, relative_path)
            
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save file
                with open(file_path, "wb") as f:
                    contenido = archivo.file.read()
                    f.write(contenido)
                
                # Validate file
                if is_valid_file(file_path, config):
                    archivos_validos.append(relative_path)
                    archivo.file.seek(0)
                else:
                    archivos_invalidos.append(relative_path)
                    os.remove(file_path)
                    # Clean empty directories
                    dir_path = os.path.dirname(file_path)
                    while dir_path != temp_dir and len(os.listdir(dir_path)) == 0:
                        os.rmdir(dir_path)
                        dir_path = os.path.dirname(dir_path)
            except Exception as e:
                print(f"Error procesando archivo {relative_path}: {str(e)}")
                archivos_invalidos.append(relative_path)
                continue

        if not archivos_validos:
            return {
                "resultado": "No se encontraron archivos válidos para procesar",
                "archivos_invalidos": archivos_invalidos,
                "extensiones_permitidas": config.allowed_extensions,
                "total_archivos": len(archivos)
            }

        # Process valid files
        mensaje, archivos_procesados = cargar_y_indexar_documentos(temp_dir, current_user.id, recursivo=True, db=db)
        
        return {
            "resultado": mensaje,
            "archivos_procesados": archivos_procesados,
            "archivos_invalidos": archivos_invalidos,
            "total_archivos": len(archivos),
            "archivos_validos": len(archivos_validos),
            "extensiones_permitidas": config.allowed_extensions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar los archivos: {str(e)}"
        )

@router.get("/documentos/listar")
def listar_documentos(current_user=Depends(require_role("superuser"))):
    """
    List all uploaded documents.
    
    Returns:
        dict: List of document paths
        
    Raises:
        HTTPException: If listing fails
    """
    try:
        carpeta = "./uploads"
        os.makedirs(carpeta, exist_ok=True)
        archivos = []
        # List files recursively
        for root, _, files in os.walk(carpeta):
            for file in files:
                # Get relative path
                ruta_completa = os.path.join(root, file)
                ruta_relativa = os.path.relpath(ruta_completa, carpeta)
                archivos.append(ruta_relativa)
        return {"documentos": archivos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documentos/eliminar/{path:path}")
def eliminar_documento(path: str, current_user=Depends(require_role("superuser"))):
    """
    Delete a document and its index.
    
    This endpoint:
    1. Removes the physical file
    2. Cleans up empty directories
    3. Removes document from search index
    
    Args:
        path (str): Path to document
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Normalize path to prevent traversal
        normalized_path = os.path.normpath(path)
        if normalized_path.startswith(".."):
            raise HTTPException(status_code=400, detail="Invalid path")
            
        file_path = os.path.join("./uploads", normalized_path)
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Archivo '{path}' no encontrado en la ruta: {file_path}")
            
        # Delete physical file
        os.remove(file_path)
        
        # Clean empty directories
        dir_path = os.path.dirname(file_path)
        while dir_path != "./uploads":
            if len(os.listdir(dir_path)) == 0:
                os.rmdir(dir_path)
            dir_path = os.path.dirname(dir_path)
        
        # Remove from vector store if supported
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.pdf', '.doc', '.docx']:
            try:
                eliminar_documento_indexado(path, current_user.id, db)
            except Exception as e:
                print(f"Error al eliminar del vectorstore: {str(e)}")
        
        return {"mensaje": f"Documento '{path}' eliminado correctamente"}
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el documento del índice: {str(e)}"
        )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado al eliminar el documento: {str(e)}"
        )

@router.post("/feedback")
def registrar_feedback_usuario(
    pregunta: str = Body(...),
    fue_util: bool = Body(...),
    llm_id: int | None = Body(None),
    current_user=Depends(require_role("user")),
    db: Session = Depends(get_db)
):
    """
    Record user feedback for a query.
    
    Args:
        pregunta (str): Original question
        fue_util (bool): Whether response was helpful
        llm_id (int, optional): LLM configuration used
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If feedback recording fails
    """
    try:
        # Log feedback in analytics
        registrar_feedback(current_user.username, pregunta, fue_util, llm_id)
        
        # Update query record with feedback
        query = db.query(Query).filter(
            Query.user_id == current_user.id,
            Query.query == pregunta,
            Query.llm_id == llm_id
        ).order_by(Query.timestamp.desc()).first()
        
        if query:
            query.feedback = "positive" if fue_util else "negative"
            db.commit()
        
        return {"mensaje": "Feedback registrado con éxito."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))