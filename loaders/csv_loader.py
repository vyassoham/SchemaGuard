"""
CSV Loader Module

Handles loading data from CSV (Comma-Separated Values) files.
Supports various CSV configurations including custom delimiters,
encoding options, and header handling.
"""

from typing import Optional, Dict, Any

import pandas as pd

from .base_loader import BaseLoader


class CSVLoader(BaseLoader):
    """
    Loader for CSV files.
    
    Supports various CSV formats with configurable options for:
    - Delimiter character
    - Encoding
    - Header row handling
    - Data type inference
    
    Example:
        >>> loader = CSVLoader("data/users.csv")
        >>> df = loader.load()
        >>> print(df.head())
    """
    
    SUPPORTED_EXTENSIONS = (".csv", ".tsv", ".txt")
    
    # Default CSV reading options
    DEFAULT_OPTIONS: Dict[str, Any] = {
        "encoding": "utf-8",
        "delimiter": ",",
        "header": 0,
        "skip_blank_lines": True,
        "na_values": ["", "NA", "N/A", "null", "NULL", "None", "none"],
    }
    
    def __init__(self, file_path: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the CSV loader.
        
        Args:
            file_path: Path to the CSV file.
            options: Optional dictionary of pandas read_csv options.
                     Supported options include:
                     - encoding: File encoding (default: utf-8)
                     - delimiter: Column separator (default: ,)
                     - header: Row number to use as header (default: 0)
                     - skip_blank_lines: Skip empty lines (default: True)
        """
        super().__init__(file_path, options)
        self._merge_default_options()
    
    def _merge_default_options(self) -> None:
        """Merge user options with defaults, user options take precedence."""
        merged = self.DEFAULT_OPTIONS.copy()
        merged.update(self.options)
        self.options = merged
    
    def _detect_delimiter(self) -> str:
        """
        Auto-detect the delimiter if not explicitly specified.
        
        Returns:
            The detected or configured delimiter character.
        """
        extension = self.file_path.suffix.lower()
        
        if extension == ".tsv":
            return "\t"
        
        # Use configured delimiter
        return self.options.get("delimiter", ",")
    
    def load(self) -> pd.DataFrame:
        """
        Load data from the CSV file into a pandas DataFrame.
        
        Returns:
            pd.DataFrame: The loaded CSV data.
        
        Raises:
            pd.errors.EmptyDataError: If the CSV file is empty.
            pd.errors.ParserError: If the CSV cannot be parsed.
        """
        # Update delimiter based on file extension
        self.options["delimiter"] = self._detect_delimiter()
        
        # Extract pandas-compatible options
        read_options = {
            "filepath_or_buffer": str(self.file_path),
            "encoding": self.options.get("encoding", "utf-8"),
            "delimiter": self.options.get("delimiter", ","),
            "header": self.options.get("header", 0),
            "skip_blank_lines": self.options.get("skip_blank_lines", True),
            "na_values": self.options.get("na_values"),
        }
        
        try:
            df = pd.read_csv(**read_options)
            
            # Clean column names: strip whitespace
            df.columns = df.columns.str.strip()
            
            return df
            
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(
                f"The CSV file is empty: {self.file_path}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load CSV file '{self.file_path}': {str(e)}"
            ) from e
    
    def preview(self, rows: int = 5) -> pd.DataFrame:
        """
        Load only the first N rows for preview.
        
        Args:
            rows: Number of rows to load (default: 5).
        
        Returns:
            pd.DataFrame: Preview of the CSV data.
        """
        read_options = {
            "filepath_or_buffer": str(self.file_path),
            "encoding": self.options.get("encoding", "utf-8"),
            "delimiter": self._detect_delimiter(),
            "header": self.options.get("header", 0),
            "nrows": rows,
        }
        
        return pd.read_csv(**read_options)
