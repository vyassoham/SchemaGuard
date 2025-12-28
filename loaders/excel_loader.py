"""
Excel Loader Module

Handles loading data from Excel files (.xlsx, .xls).
Supports multiple sheets and sheet selection options.
"""

from typing import Optional, Dict, Any, List, Union

import pandas as pd

from .base_loader import BaseLoader


class ExcelLoader(BaseLoader):
    """
    Loader for Excel files (.xlsx, .xls).
    
    Supports loading from specific sheets or all sheets at once.
    Handles Excel-specific features like multi-sheet workbooks.
    
    Example:
        >>> loader = ExcelLoader("data/employees.xlsx", options={"sheet_name": "Staff"})
        >>> df = loader.load()
        >>> print(df.head())
        
        >>> # Load all sheets as a dictionary
        >>> loader = ExcelLoader("data/employees.xlsx", options={"sheet_name": None})
        >>> all_sheets = loader.load_all_sheets()
    """
    
    SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".xlsm", ".xlsb")
    
    DEFAULT_OPTIONS: Dict[str, Any] = {
        "sheet_name": 0,  # First sheet by default
        "header": 0,
        "na_values": ["", "NA", "N/A", "null", "NULL", "None", "none"],
    }
    
    def __init__(self, file_path: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the Excel loader.
        
        Args:
            file_path: Path to the Excel file.
            options: Optional dictionary of options.
                     - sheet_name: Sheet to load (name, index, or None for all)
                     - header: Row number for column names
        """
        super().__init__(file_path, options)
        self._merge_default_options()
    
    def _merge_default_options(self) -> None:
        """Merge user options with defaults."""
        merged = self.DEFAULT_OPTIONS.copy()
        merged.update(self.options)
        self.options = merged
    
    def get_sheet_names(self) -> List[str]:
        """
        Get list of all sheet names in the Excel file.
        
        Returns:
            List of sheet names.
        """
        excel_file = pd.ExcelFile(str(self.file_path))
        return excel_file.sheet_names
    
    def load(self) -> pd.DataFrame:
        """
        Load data from the Excel file into a pandas DataFrame.
        
        If sheet_name option is None, returns the first sheet.
        For loading all sheets, use load_all_sheets() method.
        
        Returns:
            pd.DataFrame: The loaded Excel data from the specified sheet.
        
        Raises:
            ValueError: If the specified sheet does not exist.
        """
        try:
            sheet_name = self.options.get("sheet_name", 0)
            
            # If sheet_name is None, load all and return first
            if sheet_name is None:
                sheet_name = 0
            
            df = pd.read_excel(
                str(self.file_path),
                sheet_name=sheet_name,
                header=self.options.get("header", 0),
                na_values=self.options.get("na_values"),
            )
            
            # Clean column names
            if isinstance(df, pd.DataFrame):
                df.columns = df.columns.astype(str).str.strip()
            
            return df
            
        except ValueError as e:
            available_sheets = self.get_sheet_names()
            raise ValueError(
                f"Sheet not found in '{self.file_path}'. "
                f"Available sheets: {available_sheets}. Error: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Excel file '{self.file_path}': {str(e)}"
            ) from e
    
    def load_all_sheets(self) -> Dict[str, pd.DataFrame]:
        """
        Load all sheets from the Excel file.
        
        Returns:
            Dictionary mapping sheet names to DataFrames.
        """
        try:
            all_sheets = pd.read_excel(
                str(self.file_path),
                sheet_name=None,  # Load all sheets
                header=self.options.get("header", 0),
                na_values=self.options.get("na_values"),
            )
            
            # Clean column names in all sheets
            for sheet_name, df in all_sheets.items():
                df.columns = df.columns.astype(str).str.strip()
            
            return all_sheets
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Excel file '{self.file_path}': {str(e)}"
            ) from e
    
    def load_sheet_by_name(self, sheet_name: str) -> pd.DataFrame:
        """
        Load a specific sheet by name.
        
        Args:
            sheet_name: Name of the sheet to load.
        
        Returns:
            pd.DataFrame: Data from the specified sheet.
        """
        available = self.get_sheet_names()
        if sheet_name not in available:
            raise ValueError(
                f"Sheet '{sheet_name}' not found. Available: {available}"
            )
        
        df = pd.read_excel(
            str(self.file_path),
            sheet_name=sheet_name,
            header=self.options.get("header", 0),
            na_values=self.options.get("na_values"),
        )
        
        df.columns = df.columns.astype(str).str.strip()
        return df
    
    def combine_all_sheets(self) -> pd.DataFrame:
        """
        Load and combine all sheets into a single DataFrame.
        
        Adds a 'source_sheet' column to identify the origin of each row.
        
        Returns:
            pd.DataFrame: Combined data from all sheets.
        """
        all_sheets = self.load_all_sheets()
        
        combined_dfs = []
        for sheet_name, df in all_sheets.items():
            df = df.copy()
            df["_source_sheet"] = sheet_name
            combined_dfs.append(df)
        
        if not combined_dfs:
            return pd.DataFrame()
        
        return pd.concat(combined_dfs, ignore_index=True)
