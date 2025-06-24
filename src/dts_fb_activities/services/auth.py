"""Authentication service for PITB dashboard."""

import json
import requests
from typing import Optional
from ..core.config import settings


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthService:
    """Service for handling PITB dashboard authentication."""
    
    def __init__(self):
        """Initialize the authentication service."""
        self.username = settings.pitb_username
        self.password = settings.pitb_password
        self.cookie_url = settings.cookie_url
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """Validate that required credentials are available."""
        if not self.username:
            raise AuthenticationError("PITB_USERNAME environment variable is required")
        if not self.password:
            raise AuthenticationError("PITB_PASSWORD environment variable is required")
        if not self.cookie_url:
            raise AuthenticationError("COOKIE_URL environment variable is required")
    
    def get_cookie_value(self) -> str:
        """
        Retrieve authentication cookie from the cookie service.
        
        Returns:
            str: Cookie value for dashboard authentication
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Prepare authentication payload
            payload = json.dumps({
                "username": self.username,
                "password": self.password
            })
            
            # Set content type for JSON request
            headers = {"Content-Type": "application/json"}
            
            # Make authentication request
            response = requests.post(
                self.cookie_url,
                headers=headers,
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Parse response and extract cookie
            response_json = response.json()
            
            if response_json.get("success") and "cookies" in response_json:
                cookie_value = response_json["cookies"][0]["value"]
                return cookie_value
            else:
                raise AuthenticationError("Invalid response format or unsuccessful request")
                
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise AuthenticationError(f"Failed to parse authentication response: {str(e)}")


# Global auth service instance
auth_service = AuthService()
