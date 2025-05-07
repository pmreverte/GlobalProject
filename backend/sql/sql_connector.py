"""
SQL Server Connector Module

This module provides functionality for connecting to and querying SQL Server databases.
It supports both Windows Authentication and SQL Server Authentication methods,
and handles connection configuration, query execution, and result formatting.

Features:
- Dynamic configuration loading from JSON
- Support for Windows and SQL Server authentication
- Secure parameter binding for queries
- Connection pooling through SQLAlchemy
- Error handling and result formatting

Configuration:
The module expects a sql_config.json file in the config directory with the following structure:
{
    "server": "server_name",
    "database": "database_name",
    "username": "sql_user",         // Optional for Windows auth
    "password": "sql_password",     // Optional for Windows auth
    "driver": "ODBC Driver 17 for SQL Server",
    "use_windows_auth": false
}
"""

import os
import json
import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path

def get_sql_config() -> str:
    """
    Load SQL Server configuration and build connection URL.
    
    This function reads the SQL Server configuration from a JSON file
    and constructs the appropriate SQLAlchemy connection URL based on
    the authentication method specified.
    
    Returns:
        str: SQLAlchemy connection URL
        
    Raises:
        ValueError: If configuration file is missing or invalid
        
    Example Config File:
        {
            "server": "localhost",
            "database": "mydatabase",
            "username": "user",
            "password": "pass",
            "driver": "ODBC Driver 17 for SQL Server",
            "use_windows_auth": false
        }
    """
    config_path = Path("config/sql_config.json")
    if not config_path.exists():
        raise ValueError("No se ha configurado la conexión a SQL Server")
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Parse server name to handle named instances
    server = config['server']
    if '\\' in server:
        # For named instances, we need to specify the server in the query parameters
        base_server = server.split('\\')[0]
        instance = server.split('\\')[1]
        if config.get("use_windows_auth"):
            # Windows Authentication with named instance
            url = f"mssql+pyodbc://{base_server}/{config['database']}?driver={config['driver'].replace(' ', '+')}&trusted_connection=yes&server={server}"
        else:
            # SQL Server Authentication with named instance
            url = f"mssql+pyodbc://{config['username']}:{config['password']}@{base_server}/{config['database']}?driver={config['driver'].replace(' ', '+')}&server={server}"
    else:
        # For default instance
        if config.get("use_windows_auth"):
            # Windows Authentication
            url = f"mssql+pyodbc://{server}/{config['database']}?driver={config['driver'].replace(' ', '+')}&trusted_connection=yes"
        else:
            # SQL Server Authentication
            url = f"mssql+pyodbc://{config['username']}:{config['password']}@{server}/{config['database']}?driver={config['driver'].replace(' ', '+')}"
    
    return url

def get_engine():
    """
    Create a new SQLAlchemy engine instance.
    
    This function creates a new database engine using the current configuration.
    The engine manages the connection pool and provides the interface for
    executing queries.
    
    Returns:
        Engine: SQLAlchemy engine instance
        
    Raises:
        ValueError: If there's an error creating the connection
        
    Note:
        The engine is configured with connection pooling enabled by default,
        which helps manage database connections efficiently.
    """
    try:
        url = get_sql_config()
        return create_engine(url)
    except Exception as e:
        raise ValueError(f"Error al crear la conexión SQL: {str(e)}")

def test_connection() -> dict:
    """
    Test the SQL Server connection and generate embeddings for all tables.
    
    This function:
    1. Attempts to establish a connection to the SQL Server with extended timeout
    2. Executes a test query to verify connectivity
    3. If successful, triggers embedding generation for all tables in batches
    
    Returns:
        dict: Result containing:
            - success: Boolean indicating if connection was successful
            - version: SQL Server version if successful
            - error: Error message if connection fails
            - embeddings_status: Detailed status of embeddings generation if connection successful
            - progress: Progress information for embedding generation
    """
    try:
        # Create engine with extended timeout
        engine = create_engine(
            get_sql_config(),
            connect_args={'timeout': 300}  # 5 minute timeout
        )
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT @@VERSION AS Version"))
            version = result.scalar()
            
            # If connection successful, generate embeddings
            from backend.sql.sql_embeddings import generate_database_embeddings
            url = get_sql_config()
            embeddings_result = generate_database_embeddings(url)
            
            status_message = (
                f"Connection successful. SQL Server version: {version}\n"
                f"Embeddings generation: {embeddings_result['message']}\n"
                f"Progress: {embeddings_result['processed_records']}/{embeddings_result['total_records']} records"
            )
            
            return {
                "success": True,
                "version": version,
                "embeddings_status": embeddings_result['message'],
                "progress": {
                    "total": embeddings_result['total_records'],
                    "processed": embeddings_result['processed_records']
                },
                "message": status_message
            }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error inesperado: {str(e)}"
        }

def ejecutar_query(sql: str, params: dict = None) -> dict:
    """
    Execute a SQL query with optional parameters.
    
    This function executes a SQL query safely using parameter binding
    and returns the results in a structured format.
    
    Args:
        sql (str): The SQL query to execute
        params (dict, optional): Parameters to bind to the query
        
    Returns:
        dict: Query results containing:
            - columnas: List of column names
            - filas: List of dictionaries containing row data
            - error: Error message if query fails
            
    Example:
        result = ejecutar_query(
            "SELECT * FROM Users WHERE country = :country",
            {"country": "Spain"}
        )
        
    Note:
        Uses SQLAlchemy's text() for SQL injection prevention
        and proper parameter binding.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text(sql), params or {})
            columnas = result.keys()
            filas = result.fetchall()
            return {
                "columnas": columnas,
                "filas": [dict(zip(columnas, fila)) for fila in filas]
            }
    except SQLAlchemyError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Example query with parameter binding
    query = "SELECT TOP 10 * FROM Clientes WHERE Pais = :pais"
    print(ejecutar_query(query, {"pais": "España"}))
