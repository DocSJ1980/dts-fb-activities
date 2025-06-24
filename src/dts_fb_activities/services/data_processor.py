"""Data processing service for surveillance data."""

import pandas as pd
from datetime import datetime
from typing import List, Tuple
from bs4 import BeautifulSoup

from .auth import auth_service
from .scraper import scraper_service
from ..models.schemas import CombinedData, ContainerData


class DataProcessingError(Exception):
    """Custom exception for data processing errors."""
    pass


class DataProcessingService:
    """Service for processing surveillance data."""
    
    def parse_html_table_to_dataframe(self, html_content: bytes) -> pd.DataFrame:
        """
        Parse HTML table content and extract Activity ID, Latitude, and Longitude columns.
        
        Args:
            html_content (bytes): Raw HTML content
            
        Returns:
            pd.DataFrame: DataFrame with Activity ID, Latitude, and Longitude
        """
        try:
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the table
            table = soup.find('table')
            if not table:
                return pd.DataFrame()
            
            # Extract headers
            headers = []
            header_row = table.find('thead').find('tr')
            for th in header_row.find_all('th'):
                headers.append(th.get_text(strip=True))
            
            # Extract data rows
            rows_data = []
            tbody = table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    row_data = []
                    for td in row.find_all('td'):
                        # Get text content, replacing <br/> with spaces if needed
                        cell_text = td.get_text(separator=' ', strip=True)
                        row_data.append(cell_text)
                    rows_data.append(row_data)
            
            # Create DataFrame
            df = pd.DataFrame(rows_data, columns=headers)
            
            # Filter to keep only Activity ID, Latitude, and Longitude columns
            columns_to_keep = ['Activity ID', 'Latitude', 'Longitude']
            
            # Check if columns exist (handle potential column name variations)
            available_columns = []
            for col in columns_to_keep:
                # Try exact match first
                if col in df.columns:
                    available_columns.append(col)
                else:
                    # Try to find similar column names (case-insensitive, with/without spaces)
                    for df_col in df.columns:
                        if col.lower().replace(' ', '') in df_col.lower().replace(' ', ''):
                            available_columns.append(df_col)
                            break
            
            if not available_columns:
                return pd.DataFrame()
            
            # Filter DataFrame to keep only the required columns
            filtered_df = df[available_columns].copy()
            
            # Clean up latitude and longitude columns (remove extra spaces, convert to numeric)
            for col in filtered_df.columns:
                if 'latitude' in col.lower():
                    filtered_df[col] = pd.to_numeric(filtered_df[col].astype(str).str.strip(), errors='coerce')
                elif 'longitude' in col.lower():
                    filtered_df[col] = pd.to_numeric(filtered_df[col].astype(str).str.strip(), errors='coerce')
            
            # Rename Activity ID column to Activity_ID
            column_mapping = {}
            for col in filtered_df.columns:
                if 'activity' in col.lower() and 'id' in col.lower():
                    column_mapping[col] = 'Activity_ID'
            
            if column_mapping:
                filtered_df = filtered_df.rename(columns=column_mapping)
            
            return filtered_df
            
        except Exception as e:
            raise DataProcessingError(f"Failed to parse HTML table: {str(e)}")
    
    def get_filtered_surveillance_data(self, cookie_value: str, target_date: datetime,
                                     town_code: int, uc_code: int) -> pd.DataFrame:
        """
        Complete function to fetch and parse surveillance data.
        
        Args:
            cookie_value (str): Authentication cookie
            target_date (datetime): Target date
            town_code (int): Town code
            uc_code (int): UC code
            
        Returns:
            pd.DataFrame: DataFrame with Activity ID, Latitude, and Longitude only
        """
        try:
            # Fetch raw HTML data
            html_content = scraper_service.get_excel_data(cookie_value, target_date, town_code, uc_code)
            
            if html_content is None:
                return pd.DataFrame()
            
            # Parse HTML and extract required columns
            df = self.parse_html_table_to_dataframe(html_content)
            
            return df
            
        except Exception as e:
            raise DataProcessingError(f"Failed to get filtered surveillance data: {str(e)}")

    def parse_html_table(self, html_content: bytes) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Parses HTML table and returns two DataFrames:
        1. Main data without Container Tag, Checked, and Positive
        2. Container data with Activity ID, Container Tag, Checked, and Positive

        Args:
            html_content (bytes): Raw HTML content

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Main data and container data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', {'id': 'p_table'})

            if not table:
                return pd.DataFrame(), pd.DataFrame()

            main_data = []
            container_data = []

            # Find all rows in tbody
            tbody = table.find('tbody')
            if not tbody:
                return pd.DataFrame(), pd.DataFrame()

            rows = tbody.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 16:  # Skip if not enough columns
                    continue

                # Extract main data (excluding Container Tag, Checked, Positive)
                # Extract picture URL with full domain
                picture_cell = cells[15]
                picture_link = picture_cell.find('a')
                if picture_link and picture_link.get('href'):
                    picture_url = f"https://dashboard-tracking.punjab.gov.pk{picture_link.get('href')}"
                else:
                    picture_url = cells[15].get_text(strip=True)

                main_record = {
                    'Sr_No': cells[0].get_text(strip=True),
                    'Activity_ID': cells[1].get_text(strip=True),
                    'Name_of_Family_Head': cells[2].get_text(strip=True),
                    'Shop_House': cells[3].get_text(strip=True),
                    'Address': cells[4].get_text(strip=True),
                    'Locality': cells[5].get_text(strip=True),
                    'District': cells[7].get_text(strip=True),
                    'Town': cells[8].get_text(strip=True),
                    'UC': cells[9].get_text(strip=True),
                    'Tag': cells[10].get_text(strip=True),
                    'Submitted_by': cells[13].get_text(strip=True),
                    'Activity_DateTime': cells[14].get_text(strip=True),
                    'Picture': picture_url
                }
                main_data.append(main_record)

                # Extract container data
                activity_id = cells[1].get_text(strip=True)

                # Parse Container Tags (column 6)
                container_tags = []
                container_cell = cells[6]
                container_paragraphs = container_cell.find_all('p')
                for p in container_paragraphs:
                    tag_text = p.get_text(strip=True)
                    if tag_text:
                        container_tags.append(tag_text)

                # Parse Checked values (column 11)
                checked_values = []
                checked_cell = cells[11]
                checked_paragraphs = checked_cell.find_all('p')
                for p in checked_paragraphs:
                    checked_text = p.get_text(strip=True)
                    if checked_text:
                        checked_values.append(checked_text)

                # Parse Positive values (column 12)
                positive_values = []
                positive_cell = cells[12]
                positive_paragraphs = positive_cell.find_all('p')
                for p in positive_paragraphs:
                    positive_text = p.get_text(strip=True)
                    if positive_text:
                        positive_values.append(positive_text)

                # Create container records (one for each container tag)
                max_length = max(len(container_tags), len(checked_values), len(positive_values))

                for i in range(max_length):
                    container_record = {
                        'Activity_ID': activity_id,
                        'Container_Tag': container_tags[i] if i < len(container_tags) else '',
                        'Checked': checked_values[i] if i < len(checked_values) else '',
                        'Positive': positive_values[i] if i < len(positive_values) else ''
                    }
                    container_data.append(container_record)

            # Create DataFrames
            main_df = pd.DataFrame(main_data)
            container_df = pd.DataFrame(container_data)

            return main_df, container_df

        except Exception as e:
            raise DataProcessingError(f"Failed to parse HTML table: {str(e)}")

    def clean_dataframes(self, main_df: pd.DataFrame, container_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Clean and convert data types for the DataFrames.

        Args:
            main_df (pd.DataFrame): Main surveillance data
            container_df (pd.DataFrame): Container surveillance data

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Cleaned DataFrames
        """
        try:
            if not main_df.empty:
                # Convert Activity_ID to string to ensure consistency
                main_df['Activity_ID'] = main_df['Activity_ID'].astype(str)

                # Clean datetime field
                main_df['Activity_DateTime'] = main_df['Activity_DateTime'].str.replace('on ', '').str.replace(' at ', ' ')

            if not container_df.empty:
                # Convert Activity_ID to string
                container_df['Activity_ID'] = container_df['Activity_ID'].astype(str)

                # Convert Checked and Positive to numeric
                container_df['Checked'] = pd.to_numeric(container_df['Checked'], errors='coerce').fillna(0).astype(int)
                container_df['Positive'] = pd.to_numeric(container_df['Positive'], errors='coerce').fillna(0).astype(int)

            return main_df, container_df

        except Exception as e:
            raise DataProcessingError(f"Failed to clean dataframes: {str(e)}")

    def get_scrapped_data_cleaned(self, cookie_value: str, target_date: datetime,
                                town_code: int, uc_code: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Main function that returns cleaned DataFrames for a specific date, town, and UC.

        Args:
            cookie_value (str): Authentication cookie
            target_date (datetime): Target date
            town_code (int): Town code
            uc_code (int): UC code

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Cleaned main and container DataFrames
        """
        try:
            # First, get a sample page to calculate total pages
            sample_page_data = scraper_service.fetch_page_data(cookie_value, target_date, town_code, uc_code, 1)
            total_records = scraper_service.get_total_records(sample_page_data)
            total_pages = total_records // 20 + 1 if total_records > 0 else 1

            all_main_data = []
            all_container_data = []

            # Loop through all pages
            for page_number in range(1, total_pages + 1):
                # Fetch page data
                page_data = scraper_service.fetch_page_data(cookie_value, target_date, town_code, uc_code, page_number)

                # Parse the HTML table
                main_df, container_df = self.parse_html_table(page_data)

                if not main_df.empty:
                    all_main_data.append(main_df)
                if not container_df.empty:
                    all_container_data.append(container_df)

            # Concatenate all data
            if all_main_data:
                final_main_df = pd.concat(all_main_data, ignore_index=True)
            else:
                final_main_df = pd.DataFrame()

            if all_container_data:
                final_container_df = pd.concat(all_container_data, ignore_index=True)
            else:
                final_container_df = pd.DataFrame()

            # Clean the data
            return self.clean_dataframes(final_main_df, final_container_df)

        except Exception as e:
            raise DataProcessingError(f"Failed to get scrapped data: {str(e)}")

    def combine_data(self, cookie_value: str, target_date: datetime,
                    town_code: int, uc_code: int) -> Tuple[List[CombinedData], List[ContainerData]]:
        """
        Combine surveillance data with location data.

        Args:
            cookie_value (str): Authentication cookie
            target_date (datetime): Target date
            town_code (int): Town code
            uc_code (int): UC code

        Returns:
            Tuple[List[CombinedData], List[ContainerData]]: Combined and container data
        """
        try:
            # Get main and container data
            main_df, container_df = self.get_scrapped_data_cleaned(cookie_value, target_date, town_code, uc_code)

            # Get location data
            locations_df = self.get_filtered_surveillance_data(cookie_value, target_date, town_code, uc_code)

            # Merge main data with location data
            if not main_df.empty and not locations_df.empty:
                combined_df = main_df.merge(locations_df, on='Activity_ID', how='left')
            else:
                combined_df = main_df

            # Convert to Pydantic models
            combined_data = []
            for _, row in combined_df.iterrows():
                combined_data.append(CombinedData(**row.to_dict()))

            container_data = []
            for _, row in container_df.iterrows():
                container_data.append(ContainerData(**row.to_dict()))

            return combined_data, container_data

        except Exception as e:
            raise DataProcessingError(f"Failed to combine data: {str(e)}")


# Global data processing service instance
data_processor = DataProcessingService()
