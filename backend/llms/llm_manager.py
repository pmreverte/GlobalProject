"""
Language Model Manager Module

This module manages the integration with different Language Model providers (OpenAI, Anthropic)
and handles LLM configuration, instantiation, and query generation.

Features:
- Dynamic LLM configuration management through database
- Support for multiple LLM providers (OpenAI, Anthropic)
- Fallback to environment variables
- SQL generation from natural language

The module uses LangChain for consistent interface across different LLM providers
and supports runtime configuration changes through database settings.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from sqlalchemy.orm import Session
from backend.auth.models import LLMConfig
from backend.db.database import SessionLocal
from typing import Optional

def get_llm_config(llm_id: Optional[int] = None) -> LLMConfig:
    """
    Retrieve LLM configuration from database.
    
    This function fetches LLM configuration either by specific ID or default configuration.
    If no configuration is found, it falls back to environment variables.
    
    Args:
        llm_id (Optional[int]): Specific LLM configuration ID to retrieve
        
    Returns:
        LLMConfig: Configuration object with provider, model, and API settings
        
    Raises:
        ValueError: If specified configuration is not found or inactive
        
    Note:
        When no configuration is found, it creates a default configuration
        using OpenAI GPT-4 and environment variables.
    """
    db = SessionLocal()
    try:
        if llm_id:
            config = db.query(LLMConfig).filter(
                LLMConfig.id == llm_id,
                LLMConfig.is_active == True
            ).first()
            if not config:
                raise ValueError(f"LLM configuration with ID {llm_id} not found or not active")
        else:
            config = db.query(LLMConfig).filter(
                LLMConfig.is_default == True,
                LLMConfig.is_active == True
            ).first()
            
        if not config:
            # Fallback to environment variables if no configuration exists
            return LLMConfig(
                provider="openai",
                model_name="gpt-4",
                api_key=os.getenv("LLM_API_KEY"),
                temperature="0"
            )
        return config
    finally:
        db.close()

def get_llm(llm_id: int = None):
    """
    Create an LLM instance based on configuration.
    
    This function instantiates the appropriate LLM class based on the provider
    specified in the configuration. It currently supports OpenAI and Anthropic.
    
    Args:
        llm_id (int, optional): Specific LLM configuration ID to use
        
    Returns:
        Union[ChatOpenAI, ChatAnthropic]: Configured LLM instance
        
    Raises:
        ValueError: If the specified provider is not supported
        
    Example:
        llm = get_llm(llm_id=1)
        response = llm.invoke("What is the weather?")
    """
    config = get_llm_config(llm_id)
    
    provider = config.provider.lower()
    if provider == "openai":
        return ChatOpenAI(
            openai_api_key=config.api_key,
            temperature=float(config.temperature),
            model_name=config.model_name
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            anthropic_api_key=config.api_key,
            temperature=float(config.temperature),
            model_name=config.model_name or "claude-3-opus-20240229"
        )
    else:
        raise ValueError(f"Proveedor LLM no soportado: {config.provider}. Proveedores soportados: openai, anthropic")

# SQL Generation Prompt Template
sql_prompt = PromptTemplate(
    input_variables=["pregunta"],
    template="""
Eres un experto en SQL Server. Genera una consulta SQL basada en la siguiente pregunta:
Pregunta: {pregunta}
Devuelve solo el SQL sin explicaciones.
"""
)

def generar_sql_desde_pregunta(pregunta: str, llm_id: int = None) -> str:
    """
    Generate SQL query from natural language question.
    
    This function uses an LLM to convert a natural language question
    into a valid SQL query. It uses a specialized prompt template
    to guide the LLM in generating appropriate SQL.
    
    Args:
        pregunta (str): Natural language question to convert to SQL
        llm_id (int, optional): Specific LLM configuration ID to use
        
    Returns:
        str: Generated SQL query string
        
    Example:
        sql = generar_sql_desde_pregunta(
            "¿Cuántas ventas hubo en enero?",
            llm_id=1
        )
        # Returns: "SELECT COUNT(*) FROM ventas WHERE MONTH(fecha) = 1"
    """
    llm = get_llm(llm_id)
    chain = sql_prompt | llm
    respuesta = chain.invoke({"pregunta": pregunta})
    return respuesta.content.strip().strip("`")
