"""API endpoints for DTS FB Activities."""

from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Query

from ..models.schemas import (
    TownData, UCData, SurveillanceResponse,
    HealthCheckResponse
)
from ..services.auth import auth_service, AuthenticationError
from ..services.data_access import data_service, DataAccessError
from ..services.data_processor import data_processor, DataProcessingError
from ..services.cache import cache_service
from ..core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version
    )


@router.get("/towns", response_model=List[TownData])
async def get_towns():
    """
    Get all available towns with their codes.
    
    Returns:
        List[TownData]: List of all towns
    """
    try:
        # Generate cache key for towns
        cache_key = cache_service.create_key_for_towns()
        
        # Try to get from cache first, otherwise fetch and cache
        def fetch_towns():
            return data_service.get_all_towns()
        
        towns = cache_service.get_or_set(cache_key, fetch_towns, ttl=300)  # 5 minutes
        return towns
        
    except DataAccessError as e:
        raise HTTPException(status_code=500, detail=f"Data access error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/towns/{town_code}/ucs", response_model=List[UCData])
async def get_ucs_by_town(town_code: int):
    """
    Get all UCs for a specific town code.
    
    Args:
        town_code (int): The town code
        
    Returns:
        List[UCData]: List of UCs for the specified town
    """
    try:
        # Validate town code
        if not data_service.validate_town_code(town_code):
            raise HTTPException(status_code=404, detail=f"Town code {town_code} not found")
        
        # Generate cache key for UCs
        cache_key = cache_service.create_key_for_ucs(town_code)
        
        # Try to get from cache first, otherwise fetch and cache
        def fetch_ucs():
            return data_service.get_ucs_by_town_code(town_code)
        
        ucs = cache_service.get_or_set(cache_key, fetch_ucs, ttl=300)  # 5 minutes
        return ucs
        
    except DataAccessError as e:
        raise HTTPException(status_code=500, detail=f"Data access error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/surveillance-data", response_model=SurveillanceResponse)
async def get_surveillance_data(
    date: str = Query(..., description="Date in YYYY-MM-DD format", example="2025-06-23"),
    town_code: int = Query(..., description="Town code"),
    uc_code: int = Query(..., description="UC code")
):
    """
    Get combined surveillance data for a specific date, town, and UC.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        town_code (int): Town code
        uc_code (int): UC code
        
    Returns:
        SurveillanceResponse: Combined and container surveillance data
    """
    try:
        # Validate date format
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Validate town and UC codes
        if not data_service.validate_town_code(town_code):
            raise HTTPException(status_code=404, detail=f"Town code {town_code} not found")
        
        if not data_service.validate_uc_code(town_code, uc_code):
            raise HTTPException(status_code=404, detail=f"UC code {uc_code} not found for town {town_code}")
        
        # Generate cache key for this specific request
        cache_key = cache_service.create_key_for_surveillance_data(date, town_code, uc_code)
        
        # Define function to fetch surveillance data
        def fetch_surveillance_data():
            # Get authentication cookie
            try:
                cookie_value = auth_service.get_cookie_value()
            except AuthenticationError as e:
                raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
            
            # Get surveillance data
            try:
                combined_data, container_data = data_processor.combine_data(
                    cookie_value, target_date, town_code, uc_code
                )
                return SurveillanceResponse(
                    combined_data=combined_data,
                    container_data=container_data,
                    total_records=len(combined_data)
                )
            except DataProcessingError as e:
                raise HTTPException(status_code=500, detail=f"Data processing error: {str(e)}")
        
        # Try to get from cache first, otherwise fetch and cache
        return cache_service.get_or_set(cache_key, fetch_surveillance_data, ttl=300)  # 5 minutes
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Cache status endpoint
@router.get("/cache-status")
async def cache_status():
    """Endpoint to get current cache statistics."""
    return cache_service.get_stats()


# Exception handlers are defined in the main app.py file
