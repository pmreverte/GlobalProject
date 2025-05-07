"""
Document Indexing and Processing Module

This module handles document processing, indexing, and retrieval using vector embeddings.
It supports multiple document types (PDF, Word) and provides functionality for:
- Document validation and configuration
- Text extraction and chunking
- Vector embedding generation
- Similarity search
- Document management

The module uses:
- LangChain for document loading and processing
- FAISS for vector storage and similarity search
- OpenAI embeddings for vector generation
- SQLAlchemy for configuration management

Key Features:
- Configurable document processing settings
- Recursive directory processing
- Chunk-based text splitting
- Vector-based similarity search
- Document deletion and management
"""

import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from typing import List, Tuple, Optional
from datetime import datetime
from backend.db.database import get_db
from backend.auth.models import DocumentConfig, DocumentRecord, DocumentLog, User
from backend.logs.logger import registrar_accion_admin
from sqlalchemy.orm import Session

def create_document_record(db: Session, filepath: str, user_id: int) -> DocumentRecord:
    """
    Create a new document record in the database.
    
    Args:
        db (Session): Database session
        filepath (str): Path to the document file
        user_id (int): ID of the user uploading the document
        
    Returns:
        DocumentRecord: Created document record
    """
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    file_type = os.path.splitext(filepath)[1].lower()
    
    record = DocumentRecord(
        filename=filename,
        file_path=filepath,
        file_size=file_size,
        file_type=file_type,
        uploaded_by=user_id
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # Log the upload
    log = DocumentLog(
        document_id=record.id,
        user_id=user_id,
        action="upload",
        details=f"File uploaded: {filename} ({file_size} bytes)"
    )
    db.add(log)
    db.commit()
    
    # Add admin log
    registrar_accion_admin(
        usuario=db.query(User).filter_by(id=user_id).first().username,
        accion="create",
        modulo="documents",
        detalles={
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "document_id": record.id
        }
    )
    
    return record

def update_document_record(db: Session, record: DocumentRecord, is_indexed: bool = False,
                         is_deleted: bool = False, user_id: Optional[int] = None) -> None:
    """
    Update a document record and log the changes.
    
    Args:
        db (Session): Database session
        record (DocumentRecord): Document record to update
        is_indexed (bool): Whether the document is indexed
        is_deleted (bool): Whether the document is deleted
        user_id (int): ID of the user making the change
    """
    changes = []
    if is_indexed != record.is_indexed:
        record.is_indexed = is_indexed
        changes.append("indexed" if is_indexed else "unindexed")
    
    if is_deleted != record.is_deleted:
        record.is_deleted = is_deleted
        changes.append("deleted" if is_deleted else "restored")
    
    if changes:
        record.last_modified = datetime.utcnow()
        db.commit()
        
        if user_id:
            log = DocumentLog(
                document_id=record.id,
                user_id=user_id,
                action=changes[0],
                details=f"Document {', '.join(changes)}: {record.filename}"
            )
            db.add(log)
            db.commit()
            
            # Add admin log
            user = db.query(User).filter_by(id=user_id).first()
            registrar_accion_admin(
                usuario=user.username,
                accion=changes[0],
                modulo="documents",
                detalles={
                    "document_id": record.id,
                    "filename": record.filename,
                    "changes": changes,
                    "is_indexed": record.is_indexed,
                    "is_deleted": record.is_deleted
                }
            )

# Constants
VECTORSTORE_PATH = "./vectorstore/documents"

# Initialize embeddings with API key
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("LLM_API_KEY"))

def get_document_config(db: Session) -> DocumentConfig:
    """
    Retrieve or create document processing configuration.
    
    Args:
        db (Session): Database session
        
    Returns:
        DocumentConfig: Configuration object with processing settings
        
    Note:
        Creates default configuration if none exists in database
    """
    config = db.query(DocumentConfig).first()
    if not config:
        # Create default configuration if none exists
        config = DocumentConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def is_valid_file(filepath: str, config: DocumentConfig) -> bool:
    """
    Validate a file against configuration settings.
    
    Args:
        filepath (str): Path to the file to validate
        config (DocumentConfig): Configuration settings
        
    Returns:
        bool: True if file is valid, False otherwise
        
    Checks:
        - File extension against allowed extensions
        - File size against maximum size limit
    """
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    allowed_extensions = [ext.strip().lower() for ext in config.allowed_extensions.split(",")]
    
    if ext not in allowed_extensions:
        return False
    
    # Check size
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if file_size_mb > config.max_file_size:
        return False
    
    return True

def procesar_archivo(ruta: str) -> List[Document]:
    """
    Process a single file and extract its content.
    
    Args:
        ruta (str): Path to the file to process
        
    Returns:
        List[Document]: List of LangChain documents with extracted content
        
    Supports:
        - PDF files (.pdf)
        - Word documents (.doc, .docx)
    """
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(ruta)
    elif ext in [".doc", ".docx"]:
        loader = UnstructuredWordDocumentLoader(ruta)
    else:
        return []

    docs = loader.load()
    archivo = os.path.basename(ruta)
    for doc in docs:
        doc.metadata["source"] = archivo
    return docs

def cargar_y_indexar_documentos(directorio: str, user_id: int, recursivo: bool = False, db: Session = None) -> Tuple[str, List[str]]:
    """
    Load and index documents from a directory.
    
    This function processes documents, splits them into chunks,
    generates embeddings, and stores them in a FAISS vector store.
    
    Args:
        directorio (str): Directory path containing documents
        user_id (int): ID of the user uploading documents
        recursivo (bool): Whether to process subdirectories
        db (Session): Database session
        
    Returns:
        Tuple[str, List[str]]: (Status message, List of processed files)
        
    Process:
        1. Validate and load documents
        2. Split text into chunks
        3. Generate embeddings
        4. Store in FAISS index
    """
    if db is None:
        db = next(get_db())

    documentos: List[Document] = []
    archivos_procesados: List[str] = []
    config = get_document_config(db)
    archivos_encontrados = 0
    
    def procesar_directorio(dir_path: str):
        nonlocal archivos_encontrados
        for root, _, files in os.walk(dir_path):
            for archivo in files:
                archivos_encontrados += 1
                if archivos_encontrados > config.max_files_per_upload:
                    return
                
                ruta = os.path.join(root, archivo)
                if is_valid_file(ruta, config):
                    # Create document record
                    record = create_document_record(db, ruta, user_id)
                    
                    docs = procesar_archivo(ruta)
                    if docs:
                        documentos.extend(docs)
                        archivos_procesados.append(archivo)
                        # Update record as indexed
                        update_document_record(db, record, is_indexed=True, user_id=user_id)
            if not recursivo:
                break

    procesar_directorio(directorio)

    if archivos_encontrados > config.max_files_per_upload:
        return f"Se excedió el límite de {config.max_files_per_upload} archivos por carga.", []

    if not documentos:
        return "No se encontraron documentos válidos.", []

    # Split documents into chunks for better processing
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(documentos)

    # Update or create vector store
    if os.path.exists(VECTORSTORE_PATH):
        vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_documents(chunks)
    else:
        vectorstore = FAISS.from_documents(chunks, embeddings)

    vectorstore.save_local(VECTORSTORE_PATH)
    return f"{len(chunks)} fragmentos indexados con éxito.", archivos_procesados

def recuperar_contexto_desde_documentos(pregunta: str, k: int = 5) -> str:
    """
    Retrieve relevant context from indexed documents.
    
    Args:
        pregunta (str): Query to search for
        k (int): Number of relevant chunks to retrieve
        
    Returns:
        str: Combined context from relevant document chunks
        
    Note:
        Uses FAISS similarity search to find relevant text chunks
    """
    if not os.path.exists(VECTORSTORE_PATH):
        return "No hay documentos indexados."

    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    docs = vectorstore.similarity_search(pregunta, k=k)
    contexto = "\n".join([doc.page_content for doc in docs])
    return contexto

def eliminar_documento_indexado(nombre: str, user_id: int, db: Session = None) -> None:
    """
    Remove a document from the vector store and update records.
    
    Args:
        nombre (str): Name of the file to remove
        user_id (int): ID of the user deleting the document
        db (Session): Database session
        
    Raises:
        Exception: If there's an error manipulating the vector store
        
    Process:
        1. Update document record as deleted
        2. Load vector store
        3. Filter out documents matching the filename
        4. Create new vector store with remaining documents
        5. Save updated vector store
    """
    if db is None:
        db = next(get_db())
        
    if not os.path.exists(VECTORSTORE_PATH):
        # Log attempt to delete from non-existent vectorstore
        user = db.query(User).filter_by(id=user_id).first()
        registrar_accion_admin(
            usuario=user.username,
            accion="delete",
            modulo="documents",
            detalles={
                "filename": nombre,
                "status": "Vector store does not exist"
            }
        )
        return
        
    try:
        # Find and update the document record
        nombre_decodificado = os.path.basename(nombre)
        record = db.query(DocumentRecord).filter_by(filename=nombre_decodificado).first()
        
        if record:
            # Update record as deleted
            update_document_record(db, record, is_deleted=True, user_id=user_id)
            
        vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
        
        # Get just the filename without path
        from urllib.parse import unquote
        nombre_decodificado = unquote(nombre)
        nombre_archivo = os.path.basename(nombre_decodificado)
        
        documentos_actualizados = []
        for doc in vectorstore.docstore._dict.values():
            # Verify metadata and source exist before comparing
            if (not hasattr(doc, 'metadata') or
                'source' not in doc.metadata or
                doc.metadata['source'] != nombre_archivo):
                documentos_actualizados.append(doc)

        if not documentos_actualizados:
            # If no documents remain, remove the vector store directory
            import shutil
            shutil.rmtree(VECTORSTORE_PATH)
            return

        nuevo_vectorstore = FAISS.from_documents(documentos_actualizados, embeddings)
        nuevo_vectorstore.save_local(VECTORSTORE_PATH)
        
    except Exception as e:
        raise Exception(f"Error al eliminar documento del vectorstore: {str(e)}")