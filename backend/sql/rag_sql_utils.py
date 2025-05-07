"""
RAG SQL Utilities Module

This module provides utilities for processing SQL query results and generating
natural language responses using Retrieval-Augmented Generation (RAG).

The module handles:
- Converting SQL results to readable text format
- Generating natural language responses using LLMs
- Contextual response generation with SQL data

Key components:
- Result formatting for better readability
- Prompt templates for response generation
- LLM integration for natural language processing
"""

from typing import Dict
from langchain.prompts import PromptTemplate
from backend.llms.llm_manager import get_llm

from backend.sql.sql_embeddings import get_similar_records

def convertir_resultado_a_texto(resultado: Dict, incluir_similares: bool = True) -> str:
    """
    Convert SQL query results to a readable text format with optional similar records.
    
    This function takes the raw SQL query results and formats them into
    a human-readable text string, optionally enriching it with similar records
    from the vector store.
    
    Args:
        resultado (Dict): SQL query results containing:
            - columnas: List of column names
            - filas: List of row dictionaries
        incluir_similares (bool): Whether to include similar records
            
    Returns:
        str: Formatted text representation of the results
        
    Example:
        Input: {
            "columnas": ["nombre", "edad"],
            "filas": [{"nombre": "Juan", "edad": 30}]
        }
        Output: "Resumen de resultados obtenidos de la base de datos:
                - nombre: Juan, edad: 30
                
                Registros similares encontrados:
                - [Tabla: Empleados] nombre: Ana, edad: 31"
    """
    if not resultado or not resultado.get("filas"):
        return "No se encontraron resultados."

    columnas = resultado["columnas"]
    filas = resultado["filas"]

    texto = "Resumen de resultados obtenidos de la base de datos:\n"
    for fila in filas:
        linea = ", ".join(f"{col}: {fila[col]}" for col in columnas)
        texto += f"- {linea}\n"
        
    # Add similar records if requested
    if incluir_similares:
        # Convert current results to search query
        query = " ".join(str(val) for fila in filas for val in fila.values())
        similares = get_similar_records(query, k=3)
        
        if similares:
            texto += "\nRegistros similares encontrados:\n"
            for registro in similares:
                texto += f"- {registro['content']}\n"
    
    return texto.strip()

# Prompt template for natural language response generation
# This template guides the LLM in generating contextual responses
respuesta_prompt = PromptTemplate(
    input_variables=["contexto", "pregunta"],
    template="""
Usa la siguiente información recuperada de la base de datos para responder a la pregunta.

Información:
{contexto}

Pregunta:
{pregunta}

Respuesta:
"""
)

def generar_respuesta_con_contexto(pregunta: str, contexto: str, llm_id: int = None) -> str:
    """
    Generate a natural language response using context and an LLM.
    
    This function combines the provided context with the user's question
    to generate a coherent and contextually relevant response using
    a Language Model.
    
    Args:
        pregunta (str): The user's question
        contexto (str): Context information (e.g., SQL results)
        llm_id (int, optional): Specific LLM configuration ID to use
        
    Returns:
        str: Generated natural language response
        
    Process:
        1. Get appropriate LLM instance
        2. Apply prompt template with context and question
        3. Generate and format response
        
    Example:
        response = generar_respuesta_con_contexto(
            "¿Cuántos empleados hay?",
            "Resumen: - total_empleados: 150",
            llm_id=1
        )
    """
    llm = get_llm(llm_id)
    respuesta_chain = respuesta_prompt | llm
    respuesta = respuesta_chain.invoke({"pregunta": pregunta, "contexto": contexto})
    return respuesta.content.strip()
