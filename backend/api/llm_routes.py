"""
LLM Configuration API Routes Module

This module provides endpoints for managing Language Model (LLM) configurations.
It handles:
- Configuration creation and management
- Active LLM status
- Default LLM settings
- Configuration validation

The module implements a complete CRUD interface for LLM configurations
with role-based access control and proper error handling.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from backend.auth.dependencies import get_db, require_role
from backend.auth.models import LLMConfig

router = APIRouter()

class LLMConfigBase(BaseModel):
    """
    Base LLM Configuration Model
    
    Defines the common attributes for LLM configurations:
    - name: Configuration identifier
    - provider: LLM provider (e.g., OpenAI, Anthropic)
    - model_name: Specific model to use
    - api_key: Authentication key for the provider
    - temperature: Response randomness setting
    - is_active: Whether the configuration is available for use
    - is_default: Whether this is the default configuration
    """
    name: str
    provider: str
    model_name: str
    api_key: str
    temperature: str
    is_active: bool = True
    is_default: bool = False

class LLMConfigCreate(LLMConfigBase):
    """
    LLM Configuration Creation Model
    
    Used for creating new LLM configurations.
    Inherits all fields from LLMConfigBase.
    """
    pass

class LLMConfigResponse(LLMConfigBase):
    """
    LLM Configuration Response Model
    
    Extends the base model to include the database ID.
    Used for returning configuration data in API responses.
    """
    id: int

    class Config:
        from_attributes = True

@router.post("/llm/config", response_model=LLMConfigResponse)
async def create_llm_config(
    config: LLMConfigCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("superuser"))
):
    """
    Create new LLM configuration.
    
    This endpoint:
    1. Validates the configuration
    2. Handles default configuration status
    3. Creates the configuration in database
    
    Args:
        config (LLMConfigCreate): Configuration parameters
        
    Returns:
        LLMConfigResponse: Created configuration
        
    Requires:
        Superuser role
    """
    # Handle default configuration
    if config.is_default:
        existing_defaults = db.query(LLMConfig).filter(LLMConfig.is_default == True).all()
        for default_config in existing_defaults:
            default_config.is_default = False
            db.add(default_config)

    db_config = LLMConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/llm/config", response_model=List[LLMConfigResponse])
async def get_llm_configs(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("superuser"))
):
    """
    Get all LLM configurations.
    
    Returns:
        List[LLMConfigResponse]: All configurations
        
    Requires:
        Superuser role
    """
    return db.query(LLMConfig).all()

@router.get("/llm/active", response_model=List[LLMConfigResponse])
async def get_active_llms(
    db: Session = Depends(get_db)
):
    """
    Get all active LLM configurations.
    
    This endpoint returns configurations available for queries.
    
    Returns:
        List[LLMConfigResponse]: Active configurations
    """
    return db.query(LLMConfig).filter(LLMConfig.is_active == True).all()

@router.get("/llm/has-active")
async def has_active_llms(
    db: Session = Depends(get_db)
):
    """
    Check if any active LLMs exist.
    
    This endpoint verifies system readiness for queries.
    
    Returns:
        dict: Status indicating if active LLMs exist
    """
    active_llm_exists = db.query(LLMConfig).filter(LLMConfig.is_active == True).first() is not None
    return {"has_active_llms": active_llm_exists}

@router.put("/llm/config/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: int,
    config: LLMConfigCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("superuser"))
):
    """
    Update existing LLM configuration.
    
    This endpoint:
    1. Validates the configuration exists
    2. Handles default configuration status
    3. Updates the configuration
    
    Args:
        config_id (int): Configuration ID to update
        config (LLMConfigCreate): Updated parameters
        
    Returns:
        LLMConfigResponse: Updated configuration
        
    Raises:
        HTTPException: If configuration not found
        
    Requires:
        Superuser role
    """
    db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="LLM configuration not found")

    # Handle default configuration
    if config.is_default:
        existing_defaults = db.query(LLMConfig).filter(
            LLMConfig.is_default == True,
            LLMConfig.id != config_id
        ).all()
        for default_config in existing_defaults:
            default_config.is_default = False
            db.add(default_config)

    for key, value in config.model_dump().items():
        setattr(db_config, key, value)

    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.delete("/llm/config/{config_id}")
async def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role("superuser"))
):
    """
    Delete LLM configuration.
    
    Args:
        config_id (int): Configuration ID to delete
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If configuration not found
        
    Requires:
        Superuser role
    """
    db_config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="LLM configuration not found")

    db.delete(db_config)
    db.commit()
    return {"message": "Configuration deleted successfully"}

@router.get("/llm/config/default", response_model=LLMConfigResponse)
async def get_default_llm_config(
    db: Session = Depends(get_db)
):
    """
    Get default LLM configuration.
    
    This endpoint returns the active default configuration
    used when no specific configuration is requested.
    
    Returns:
        LLMConfigResponse: Default configuration
        
    Raises:
        HTTPException: If no default configuration exists
    """
    default_config = db.query(LLMConfig).filter(
        LLMConfig.is_default == True,
        LLMConfig.is_active == True
    ).first()
    if not default_config:
        raise HTTPException(status_code=404, detail="No default LLM configuration found")
    return default_config