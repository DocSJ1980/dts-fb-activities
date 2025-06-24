"""Data access service for town and UC data."""

import pandas as pd
from typing import List, Tuple, Optional
from ..core.config import get_data_file_path
from ..models.schemas import TownData, UCData


class DataAccessError(Exception):
    """Custom exception for data access errors."""
    pass


class DataAccessService:
    """Service for accessing town and UC data from Excel file."""
    
    def __init__(self):
        """Initialize the data access service."""
        self.data_file_path = get_data_file_path()
        self._town_data: Optional[pd.DataFrame] = None
        self._uc_data: Optional[pd.DataFrame] = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load town and UC data from Excel file."""
        try:
            # Read the 'town' sheet
            self._town_data = pd.read_excel(
                self.data_file_path,
                sheet_name='town',
                usecols=['town_name', 'town_code']
            )
            
            # Read the 'uc' sheet
            self._uc_data = pd.read_excel(
                self.data_file_path,
                sheet_name='uc',
                usecols=['uc_name', 'town_code', 'uc_code']
            )
            
            # Validate data
            if self._town_data.empty:
                raise DataAccessError("Town data is empty")
            if self._uc_data.empty:
                raise DataAccessError("UC data is empty")
                
        except FileNotFoundError:
            raise DataAccessError(f"Data file not found: {self.data_file_path}")
        except Exception as e:
            raise DataAccessError(f"Failed to load data: {str(e)}")
    
    def get_all_towns(self) -> List[TownData]:
        """
        Get all towns data.
        
        Returns:
            List[TownData]: List of all towns with their codes
        """
        try:
            towns = []
            for _, row in self._town_data.iterrows():
                towns.append(TownData(
                    town_name=row['town_name'],
                    town_code=int(row['town_code'])
                ))
            return towns
        except Exception as e:
            raise DataAccessError(f"Failed to get towns data: {str(e)}")
    
    def get_ucs_by_town_code(self, town_code: int) -> List[UCData]:
        """
        Get all UCs for a specific town code.
        
        Args:
            town_code (int): The town code to filter by
            
        Returns:
            List[UCData]: List of UCs for the specified town
        """
        try:
            filtered_ucs = self._uc_data[self._uc_data['town_code'] == town_code]
            
            ucs = []
            for _, row in filtered_ucs.iterrows():
                ucs.append(UCData(
                    uc_name=row['uc_name'],
                    town_code=int(row['town_code']),
                    uc_code=int(row['uc_code'])
                ))
            return ucs
        except Exception as e:
            raise DataAccessError(f"Failed to get UCs for town {town_code}: {str(e)}")
    
    def validate_town_code(self, town_code: int) -> bool:
        """
        Validate if a town code exists.
        
        Args:
            town_code (int): The town code to validate
            
        Returns:
            bool: True if town code exists, False otherwise
        """
        return town_code in self._town_data['town_code'].values
    
    def validate_uc_code(self, town_code: int, uc_code: int) -> bool:
        """
        Validate if a UC code exists for a specific town.
        
        Args:
            town_code (int): The town code
            uc_code (int): The UC code to validate
            
        Returns:
            bool: True if UC code exists for the town, False otherwise
        """
        filtered_ucs = self._uc_data[
            (self._uc_data['town_code'] == town_code) &
            (self._uc_data['uc_code'] == uc_code)
        ]
        return not filtered_ucs.empty
    
    def get_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get raw DataFrames for internal use.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Town data and UC data DataFrames
        """
        return self._town_data.copy(), self._uc_data.copy()


# Global data access service instance
data_service = DataAccessService()
