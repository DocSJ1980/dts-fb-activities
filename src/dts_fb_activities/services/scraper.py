"""Web scraping service for PITB dashboard data."""

import re
import requests
from datetime import datetime
from typing import Optional
from ..core.config import settings


class ScrapingError(Exception):
    """Custom exception for scraping errors."""
    pass


class ScrapingService:
    """Service for scraping data from PITB dashboard."""
    
    def __init__(self):
        """Initialize the scraping service."""
        self.district_id = settings.district_id
        self.report_type = settings.report_type
    
    def fetch_page_data(self, cookie_value: str, target_date: datetime, 
                       town_code: int, uc_code: int, page_number: int = 1) -> bytes:
        """
        Fetch page data from the dashboard API.
        
        Args:
            cookie_value (str): Authentication cookie value
            target_date (datetime): Target date for data
            town_code (int): Town code
            uc_code (int): UC code
            page_number (int): Page number for pagination
            
        Returns:
            bytes: Raw HTML content
            
        Raises:
            ScrapingError: If scraping fails
        """
        try:
            formatted_date = target_date.strftime("%Y-%m-%d")
            
            headers = {"Cookie": f"_dengue_new_session={cookie_value}"}
            
            url = (
                f"https://dashboard-tracking.punjab.gov.pk/activities/vector_surveillances/line_list"
                f"?activity_type={self.report_type}"
                f"&datefrom={formatted_date}T00%3A00"
                f"&dateto={formatted_date}T23%3A59"
                f"&district_id={self.district_id}"
                f"&larvae_found="
                f"&page={page_number}"
                f"&tehsil_id={town_code}"
                f"&uc={uc_code}"
            )
            
            response = requests.get(url, headers=headers, data={}, verify=False, timeout=30)
            
            # Check if we got redirected to login page
            if "login" in response.url.lower() or "sign in" in response.text.lower():
                raise ScrapingError("Authentication failed - redirected to login page")
            
            response.raise_for_status()
            return response.content
            
        except requests.RequestException as e:
            raise ScrapingError(f"Failed to fetch page data: {str(e)}")
    
    def get_excel_data(self, cookie_value: str, target_date: datetime,
                      town_code: int, uc_code: int) -> bytes:
        """
        Fetch Excel data from the dashboard API.
        
        Args:
            cookie_value (str): Authentication cookie value
            target_date (datetime): Target date for data
            town_code (int): Town code
            uc_code (int): UC code
            
        Returns:
            bytes: Raw HTML content with location data
            
        Raises:
            ScrapingError: If scraping fails
        """
        try:
            formatted_date = target_date.strftime("%Y-%m-%d")
            
            headers = {"Cookie": f"_dengue_new_session={cookie_value}"}
            
            url = (
                f"https://dashboard-tracking.punjab.gov.pk//activities/vector_surveillances/line_list"
                f"?action=line_list"
                f"&activity_type={self.report_type}"
                f"&controller=activities%2Fvector_surveillances"
                f"&datefrom={formatted_date}T00%3A00"
                f"&dateto={formatted_date}T23%3A59"
                f"&district_id={self.district_id}"
                f"&format=xls"
                f"&larvae_found="
                f"&page=1"
                f"&pagination=No"
                f"&tehsil_id={town_code}"
                f"&uc={uc_code}"
            )
            
            response = requests.get(url, headers=headers, data={}, verify=False, timeout=30)
            
            # Check if we got redirected to login page
            if "login" in response.url.lower() or "sign in" in response.text.lower():
                raise ScrapingError("Authentication failed - redirected to login page")
            
            response.raise_for_status()
            return response.content
            
        except requests.RequestException as e:
            raise ScrapingError(f"Failed to fetch Excel data: {str(e)}")
    
    def get_total_records(self, page_data: bytes) -> int:
        """
        Extract total records count from page data.
        
        Args:
            page_data (bytes): Raw HTML page data
            
        Returns:
            int: Total number of records
        """
        try:
            # Extract the number after "Total Records:"
            match = re.search(r'Total Records:\s*</b>\s*(\d+)', page_data.decode('utf-8'))
            if match:
                return int(match.group(1))
            else:
                return 0
        except Exception:
            return 0


# Global scraping service instance
scraper_service = ScrapingService()
