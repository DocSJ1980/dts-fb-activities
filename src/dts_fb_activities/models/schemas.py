"""Pydantic models for API request/response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TownData(BaseModel):
    """Model for town data."""
    town_name: str = Field(..., description="Name of the town")
    town_code: int = Field(..., description="Unique code for the town")


class UCData(BaseModel):
    """Model for UC (Union Council) data."""
    uc_name: str = Field(..., description="Name of the UC")
    town_code: int = Field(..., description="Code of the town this UC belongs to")
    uc_code: int = Field(..., description="Unique code for the UC")


class ContainerData(BaseModel):
    """Model for container surveillance data."""
    Activity_ID: str = Field(..., description="Unique activity identifier")
    Container_Tag: str = Field(..., description="Type of container")
    Checked: int = Field(..., description="Number of containers checked")
    Positive: int = Field(..., description="Number of positive containers")


class CombinedData(BaseModel):
    """Model for combined surveillance data."""
    Sr_No: str = Field(..., description="Serial number")
    Activity_ID: str = Field(..., description="Unique activity identifier")
    Name_of_Family_Head: str = Field(..., description="Name of family head")
    Shop_House: str = Field(..., description="Shop or house number")
    Address: str = Field(..., description="Address")
    Locality: str = Field(..., description="Locality name")
    District: str = Field(..., description="District name")
    Town: str = Field(..., description="Town name")
    UC: str = Field(..., description="UC name")
    Tag: str = Field(..., description="Activity tag")
    Submitted_by: str = Field(..., description="Submitted by user ID")
    Activity_DateTime: str = Field(..., description="Activity date and time")
    Picture: str = Field(..., description="Picture status")
    Latitude: Optional[float] = Field(None, description="Latitude coordinate")
    Longitude: Optional[float] = Field(None, description="Longitude coordinate")


class SurveillanceRequest(BaseModel):
    """Model for surveillance data request."""
    date: str = Field(..., description="Date in YYYY-MM-DD format", example="2025-06-23")
    town_code: int = Field(..., description="Town code")
    uc_code: int = Field(..., description="UC code")


class SurveillanceResponse(BaseModel):
    """Model for surveillance data response."""
    combined_data: List[CombinedData] = Field(..., description="Combined surveillance data")
    container_data: List[ContainerData] = Field(..., description="Container surveillance data")
    total_records: int = Field(..., description="Total number of records")


class HealthCheckResponse(BaseModel):
    """Model for health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
