"""
Main Application Module

This is the entry point for the FastAPI application. It sets up:
- Application configuration
- CORS middleware
- Route registration
- API documentation

The application integrates multiple components:
- Authentication system
- Admin management
- User operations
- Query processing
- LLM (Language Model) integration
- Analytics tracking

The API is structured with a modular approach, where each component
has its own router for better organization and maintainability.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from backend.api import admin_routes, user_routes, query_routes, llm_routes, analytics_routes
from backend.auth.auth_system import router as auth_router

# Initialize FastAPI application
# - title: Application name shown in API docs
# - root_path: Base path for all routes
app = FastAPI(title="Agente de IA Multifuente", root_path="/api")

# Configure CORS middleware
# This allows the frontend to communicate with the API
# Security Note: In production, replace "*" with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Register route handlers
# Each router handles a specific aspect of the application:
# - auth_router: Authentication and authorization
# - admin_routes: Administrative operations
# - user_routes: User-related operations
# - query_routes: Query processing and execution
# - llm_routes: Language model integration
# - analytics_routes: Usage tracking and analytics
app.include_router(auth_router)
app.include_router(admin_routes.router)
app.include_router(user_routes.router)
app.include_router(query_routes.router)
app.include_router(llm_routes.router)
app.include_router(analytics_routes.router)

@app.get("/")
def read_root():
    """
    Root endpoint to verify API status.
    
    Returns:
        dict: A simple message indicating the API is active
        
    Example:
        Response: {"message": "Agente de IA Multifuente activo"}
    """
    return {"message": "Agente de IA Multifuente activo"}

# Note: To run the application:
# uvicorn main:app --reload
# This will start the development server with auto-reload enabled
