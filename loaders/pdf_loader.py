"""
PDF Loader Module

Handles extracting tabular data from PDF files.
Uses tabula-py for table extraction from structured PDFs.

IMPORTANT LIMITATIONS:
- Only works with structured tables in PDFs
- May not work well with scanned documents (images)
- Table detection depends on PDF structure
- Complex layouts may produce inconsistent results
"""

from typing import Optional, Dict, Any, List
import warnings

import pandas as pd

from .base_loader import BaseLoader


# Attempt to import tabula
try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False
    warnings.warn(
        "tabula-py is not installed. PDF loading will not be available. "
        "Install with: pip install tabula-py"
    )


class PDFLoader(BaseLoader):
    """
    Loader for PDF files containing structured tables.
    
    Uses tabula-py to extract tables from PDFs and convert them
    to pandas DataFrames. Best suited for PDFs with clearly
    defined table structures.
    
    LIMITATIONS:
    - Requires Java to be installed (tabula-py dependency)
    - Works best with text-based PDFs, not scanned images
    - Complex table layouts may not be extracted correctly
    - Multi-page tables may require manual configuration
    
    Example:
        >>> loader = PDFLoader("data/report.pdf")
        >>> df = loader.load()  # Loads first table found
        >>> print(df.head())
        
        >>> # Load all tables from the PDF
        >>> all_tables = loader.load_all_tables()
    """
    
    SUPPORTED_EXTENSIONS = (".pdf",)
    
    DEFAULT_OPTIONS: Dict[str, Any] = {
        "pages": "all",
        "multiple_tables": True,
        "lattice": False,  # Use stream mode by default
        "guess": True,
    }
    
    def __init__(self, file_path: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the PDF loader.
        
        Args:
            file_path: Path to the PDF file.
            options: Optional dictionary of options.
                     - pages: Pages to extract ("all", "1", "1-3", etc.)
                     - multiple_tables: Whether to extract multiple tables
                     - lattice: Use lattice mode for tables with borders
                     - guess: Guess table areas automatically
        
        Raises:
            ImportError: If tabula-py is not installed.
        """
        if not TABULA_AVAILABLE:
            raise ImportError(
                "tabula-py is required for PDF loading. "
                "Install with: pip install tabula-py\n"
                "Note: Java must also be installed on your system."
            )
        
        super().__init__(file_path, options)
        self._merge_default_options()
    
    def _merge_default_options(self) -> None:
        """Merge user options with defaults."""
        merged = self.DEFAULT_OPTIONS.copy()
        merged.update(self.options)
        self.options = merged
    
    def _extract_tables(self) -> List[pd.DataFrame]:
        """
        Extract all tables from the PDF.
        
        Returns:
            List of DataFrames, one per table found.
        """
        try:
            tables = tabula.read_pdf(
                str(self.file_path),
                pages=self.options.get("pages", "all"),
                multiple_tables=self.options.get("multiple_tables", True),
                lattice=self.options.get("lattice", False),
                guess=self.options.get("guess", True),
                silent=True,
            )
            
            return tables if tables else []
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to extract tables from PDF '{self.file_path}': {str(e)}\n"
                f"Ensure Java is installed and the PDF contains structured tables."
            ) from e
    
    def load(self) -> pd.DataFrame:
        """
        Load the first table from the PDF file.
        
        If multiple tables are found, returns only the first one.
        Use load_all_tables() to get all tables.
        
        Returns:
            pd.DataFrame: The first table found in the PDF.
        
        Raises:
            ValueError: If no tables are found in the PDF.
            RuntimeError: If table extraction fails.
        """
        tables = self._extract_tables()
        
        if not tables:
            raise ValueError(
                f"No tables found in PDF '{self.file_path}'. "
                f"This loader only works with PDFs containing structured tables. "
                f"Scanned documents or complex layouts may not be supported."
            )
        
        # Return the first table
        df = tables[0]
        
        # Clean the DataFrame
        df = self._clean_dataframe(df)
        
        return df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the extracted DataFrame.
        
        Args:
            df: DataFrame to clean.
        
        Returns:
            Cleaned DataFrame.
        """
        if df.empty:
            return df
        
        # Convert column names to strings and strip whitespace
        df.columns = df.columns.astype(str).str.strip()
        
        # Replace common null representations
        df = df.replace(
            to_replace=["", "nan", "NaN", "NAN", "null", "NULL", "None", "-"],
            value=pd.NA
        )
        
        # Strip whitespace from string columns
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace("nan", pd.NA)
        
        # Drop completely empty rows
        df = df.dropna(how="all")
        
        return df
    
    def load_all_tables(self) -> List[pd.DataFrame]:
        """
        Load all tables from the PDF.
        
        Returns:
            List of DataFrames, one per table found.
        
        Raises:
            ValueError: If no tables are found.
        """
        tables = self._extract_tables()
        
        if not tables:
            raise ValueError(
                f"No tables found in PDF '{self.file_path}'."
            )
        
        # Clean all tables
        return [self._clean_dataframe(df) for df in tables]
    
    def combine_all_tables(self) -> pd.DataFrame:
        """
        Load and combine all tables into a single DataFrame.
        
        Tables with matching columns are concatenated.
        A '_table_index' column is added to identify source tables.
        
        Returns:
            pd.DataFrame: Combined data from all tables.
        """
        tables = self.load_all_tables()
        
        combined_dfs = []
        for idx, df in enumerate(tables):
            df = df.copy()
            df["_table_index"] = idx
            combined_dfs.append(df)
        
        if not combined_dfs:
            return pd.DataFrame()
        
        return pd.concat(combined_dfs, ignore_index=True)
    
    def get_table_count(self) -> int:
        """
        Get the number of tables detected in the PDF.
        
        Returns:
            Number of tables found.
        """
        tables = self._extract_tables()
        return len(tables)
    
    def get_extraction_info(self) -> Dict[str, Any]:
        """
        Get information about the extraction results.
        
        Returns:
            Dictionary with extraction metadata.
        """
        try:
            tables = self._extract_tables()
            return {
                "file_path": str(self.file_path),
                "tables_found": len(tables),
                "table_shapes": [df.shape for df in tables],
                "table_columns": [list(df.columns) for df in tables],
            }
        except Exception as e:
            return {
                "file_path": str(self.file_path),
                "error": str(e),
            }
