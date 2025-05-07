"""
SQL Embeddings Management Module

This module handles the generation and management of embeddings for SQL table records.
It provides functionality for:
- Generating embeddings for all records in specified tables
- Storing embeddings in FAISS vector store
- Managing and updating embeddings when data changes
- Integration with RAG system for query processing

Key components:
- Table record processing
- Embedding generation
- Vector store management
- Record tracking
"""

import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from sqlalchemy import create_engine, text, MetaData, inspect
from datetime import datetime
from backend.sql.sql_connector import get_sql_config
from backend.logs.logger import registrar_accion_admin

# Constants
VECTORSTORE_PATH = "./vectorstore/sql"
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("LLM_API_KEY"))

def get_all_tables(engine) -> List[str]:
    """
    Get all table names from the connected database.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        List[str]: List of table names
    """
    inspector = inspect(engine)
    return inspector.get_table_names()

from typing import List, Dict, Any, Tuple
import tiktoken

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text using tiktoken.
    
    Args:
        text (str): Text to count tokens for
        
    Returns:
        int: Number of tokens
    """
    encoding = tiktoken.get_encoding("cl100k_base")  # encoding used by text-embedding-ada-002
    return len(encoding.encode(text))

def format_record_text(table_name: str, record: Dict[str, Any], max_field_length: int = 1000) -> str:
    """
    Format a database record as text for embedding generation.
    
    Args:
        table_name (str): Name of the table
        record (Dict): Record data
        max_field_length (int): Maximum length for each field value
        
    Returns:
        str: Formatted text representation of the record
    """
    # Format each field with length limit
    fields = []
    for k, v in record.items():
        if v is not None:
            # Convert to string and limit length
            v_str = str(v)
            if len(v_str) > max_field_length:
                v_str = v_str[:max_field_length] + "..."
            fields.append(f"{k}: {v_str}")
    
    # Combine into readable text
    return f"Table: {table_name}\n" + "\n".join(fields)

def chunk_text(text: str, max_tokens: int = 250000) -> List[str]:
    """
    Split text into chunks that don't exceed the token limit.
    
    Args:
        text (str): Text to chunk
        max_tokens (int): Maximum tokens per chunk
        
    Returns:
        List[str]: List of text chunks
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return [text]
        
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Split on newlines to keep record structure
    lines = text.split('\n')
    header = lines[0]  # Keep the "Table: xxx" line
    
    for line in lines[1:]:
        line_tokens = len(encoding.encode(line))
        
        if current_length + line_tokens > max_tokens:
            # Start new chunk
            if current_chunk:
                chunks.append(header + '\n' + '\n'.join(current_chunk))
            current_chunk = [line]
            current_length = len(encoding.encode(header)) + line_tokens
        else:
            current_chunk.append(line)
            current_length += line_tokens
    
    if current_chunk:
        chunks.append(header + '\n' + '\n'.join(current_chunk))
    
    return chunks

def process_table(engine, table_name: str) -> List[Document]:
    """
    Process all records in a table and convert them to documents.
    
    Args:
        engine: SQLAlchemy engine instance
        table_name (str): Name of the table to process
        
    Returns:
        List[Document]: List of documents ready for embedding
    """
    documents = []
    
    with engine.connect() as conn:
        # Get all records from the table
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        columns = result.keys()
        
        for row in result:
            record = dict(zip(columns, row))
            text_content = format_record_text(table_name, record)
            
            # Create document with metadata
            doc = Document(
                page_content=text_content,
                metadata={
                    "table": table_name,
                    "record_id": str(record.get("id", "unknown")),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            documents.append(doc)
            
    return documents

def generate_database_embeddings(connection_url: str, batch_size: int = 1000) -> dict:
    """
    Generate embeddings for all records in all tables.
    
    Args:
        connection_url (str): Database connection URL
        batch_size (int): Number of records to process in each batch
        
    Returns:
        dict: Status information including progress and completion details
        
    Process:
        1. Connect to database
        2. Get all tables
        3. Process each table's records in batches
        4. Generate embeddings
        5. Store in FAISS index
    """
    try:
        engine = create_engine(connection_url, pool_timeout=300)  # 5 minute timeout
        tables = get_all_tables(engine)
        
        total_records = 0
        processed_records = 0
        all_documents = []
        
        # First count total records
        for table in tables:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    total_records += count
            except Exception as e:
                print(f"Error counting records in table {table}: {str(e)}")
                continue
        
        # Process tables in batches
        for table in tables:
            try:
                with engine.connect() as conn:
                    # Get total records for this table
                    offset = 0
                    while True:
                        # Process batch
                        query = text(f"SELECT * FROM {table} ORDER BY (SELECT NULL) OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY")
                        result = conn.execute(query)
                        
                        if not result:
                            break
                            
                        batch_records = []
                        columns = result.keys()
                        for row in result:
                            record = dict(zip(columns, row))
                            text_content = format_record_text(table, record, max_field_length=1000)
                            
                            # Split into chunks if needed
                            chunks = chunk_text(text_content, max_tokens=200000)  # Reduced from 250k to be safe
                            for i, chunk in enumerate(chunks):
                                doc = Document(
                                    page_content=chunk,
                                    metadata={
                                        "table": table,
                                        "record_id": str(record.get("id", "unknown")),
                                        "chunk": i + 1 if len(chunks) > 1 else None,
                                        "total_chunks": len(chunks),
                                        "timestamp": datetime.utcnow().isoformat()
                                    }
                                )
                                batch_records.append(doc)
                            processed_records += 1
                        
                        if not batch_records:
                            break
                            
                        # Process in smaller chunks to avoid token limits
                        chunk_size = 50  # Process 50 documents at a time
                        for i in range(0, len(batch_records), chunk_size):
                            chunk_docs = batch_records[i:i + chunk_size]
                            try:
                                if os.path.exists(VECTORSTORE_PATH):
                                    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
                                    vectorstore.add_documents(chunk_docs)
                                else:
                                    vectorstore = FAISS.from_documents(chunk_docs, embeddings)
                                vectorstore.save_local(VECTORSTORE_PATH)
                                all_documents.extend(chunk_docs)
                            except Exception as e:
                                print(f"Error processing chunk in table {table}: {str(e)}")
                                continue
                        
                        offset += batch_size
                        
                        # Return progress
                        progress = (processed_records / total_records) * 100 if total_records > 0 else 0
                        print(f"Progress: {progress:.2f}% ({processed_records}/{total_records} records)")
                        
            except Exception as e:
                print(f"Error processing table {table}: {str(e)}")
                continue
        
        if not all_documents:
            return {
                "status": "warning",
                "message": "No records found to process.",
                "total_records": 0,
                "processed_records": 0
            }
            
        return {
            "status": "success",
            "message": f"Successfully generated embeddings for {processed_records} records from {len(tables)} tables.",
            "total_records": total_records,
            "processed_records": processed_records
        }
        
    except Exception as e:
        error_msg = f"Error generating database embeddings: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "total_records": total_records if 'total_records' in locals() else 0,
            "processed_records": processed_records if 'processed_records' in locals() else 0
        }

def get_similar_records(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve similar records based on a query.
    
    Args:
        query (str): Search query
        k (int): Number of records to retrieve
        
    Returns:
        List[Dict]: List of similar records with metadata
    """
    if not os.path.exists(VECTORSTORE_PATH):
        return []
        
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
    docs = vectorstore.similarity_search(query, k=k)
    
    results = []
    for doc in docs:
        results.append({
            "content": doc.page_content,
            "table": doc.metadata.get("table"),
            "record_id": doc.metadata.get("record_id"),
            "timestamp": doc.metadata.get("timestamp")
        })
        
    return results