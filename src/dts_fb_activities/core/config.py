"""Configuration management for the application."""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    app_name: str = Field(default="DTS FB Activities API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # PITB Authentication
    pitb_username: Optional[str] = Field(default=None, env="PITB_USERNAME", description="PITB username")
    pitb_password: Optional[str] = Field(default=None, env="PITB_PASSWORD", description="PITB password")
    cookie_url: Optional[str] = Field(default=None, env="COOKIE_URL", description="Cookie service URL")
    
    # Data Configuration
    report_type: str = Field(default="indoor", description="Report type")
    district_id: int = Field(default=31, description="District ID for Rawalpindi")
    
    # File paths
    data_file_path: str = Field(
        default="town-uc-codes.xlsx",
        description="Path to town-uc-codes.xlsx file"
    )
    
    # API Configuration
    cors_origins: list = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Global settings instance
settings = get_settings()


def get_data_file_path() -> Path:
    """Get the absolute path to the data file."""
    # Get the project root directory
    current_file = Path(__file__)
    # Assuming the script is in src/dts_fb_activities/core
    # and the data file is in src/dts_fb_activities
    data_dir = current_file.parent.parent
    data_path = data_dir / settings.data_file_path
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found at: {data_path}")
    
    return data_path
