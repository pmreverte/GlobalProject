"""
Query Router Module

This module implements the core query processing pipeline that combines multiple data sources
to answer user questions. It orchestrates:
1. SQL query generation and execution
2. Document context retrieval
3. Context combination
4. LLM-based response generation

The module integrates several components:
- LLM Manager for SQL generation
- SQL Connector for database queries
- Document Indexer for relevant document retrieval
- RAG (Retrieval-Augmented Generation) utilities

This implementation follows a RAG pattern where both structured (SQL)
and unstructured (documents) data are combined to provide comprehensive answers.
"""

from backend.llms.llm_manager import generar_sql_desde_pregunta
from backend.sql.sql_connector import ejecutar_query
from backend.sql.rag_sql_utils import convertir_resultado_a_texto
from backend.sql.rag_sql_utils import generar_respuesta_con_contexto
from backend.documents.doc_indexer import recuperar_contexto_desde_documentos
from backend.sql.sql_embeddings import get_similar_records


def responder_a_pregunta_combinada(pregunta: str, llm_id: int = None) -> dict:
    """
    Process a user question using multiple data sources and generate a comprehensive response.
    
    This function implements a multi-step pipeline:
    1. Check SQL embeddings for similar records
    2. If no relevant embeddings, generate and execute SQL query
    3. Retrieve relevant context from indexed documents
    4. Combine contexts
    5. Generate a natural language response using an LLM
    
    Args:
        pregunta (str): The user's question in natural language
        llm_id (int, optional): Specific LLM configuration ID to use. Defaults to None.
        
    Returns:
        dict: A response object containing:
            - pregunta: Original question
            - sql_generado: Generated SQL query
            - respuesta: Final natural language response
            - fuente: Source data used (SQL results and document excerpts)
            - error_details: Any errors encountered (if any)
    """
    error_details = {}
    
    # 1. Check SQL Embeddings
    registros_similares = get_similar_records(pregunta, k=10)
    if registros_similares:
        # Use embeddings directly if found
        contexto_sql = "Información encontrada en la base de datos:\n"
        for registro in registros_similares:
            contexto_sql += f"- {registro['content']}\n"
        sql = "Consulta respondida usando embeddings"
        resultado_sql = {"embeddings": registros_similares}
    else:
        # 2. SQL Context Retrieval if no embeddings found
        try:
            sql = generar_sql_desde_pregunta(pregunta, llm_id)
            resultado_sql = ejecutar_query(sql)
            contexto_sql = convertir_resultado_a_texto(resultado_sql, incluir_similares=False)
        except Exception as e:
            error_details['sql_error'] = str(e)
            contexto_sql = f"[ERROR SQL] {str(e)}"
            resultado_sql = {}
            sql = None

    # 3. Document Context Retrieval
    try:
        contexto_docs = recuperar_contexto_desde_documentos(pregunta)
    except Exception as e:
        error_details['docs_error'] = str(e)
        contexto_docs = f"[ERROR DOCS] {str(e)}"

    # 4. Context Combination
    contexto_completo = f"### Datos de SQL Server:\n{contexto_sql}\n\n### Datos de Documentos:\n{contexto_docs}"

    # 5. LLM Response Generation
    try:
        respuesta = generar_respuesta_con_contexto(pregunta, contexto_completo, llm_id)
    except Exception as e:
        error_details['llm_error'] = str(e)
        respuesta = f"Error al generar respuesta: {str(e)}"
        
    if error_details and not respuesta or respuesta.startswith("Error al generar respuesta"):
        raise Exception(f"Errores en el proceso: {str(error_details)}")

    return {
        "pregunta": pregunta,
        "sql_generado": sql,
        "respuesta": respuesta,
        "fuente": {
            "sql": resultado_sql,
            "documentos": contexto_docs[:1000]
        },
        "error_details": error_details if error_details else None
    }
