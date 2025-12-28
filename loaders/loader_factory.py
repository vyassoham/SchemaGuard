"""
Loader Factory Module

Factory pattern implementation for automatic loader selection
based on file extension. Provides a unified interface for loading
data from any supported file format.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Type

import pandas as pd

from .base_loader import BaseLoader
from .csv_loader import CSVLoader
from .excel_loader import ExcelLoader
from .json_loader import JSONLoader
from .pdf_loader import PDFLoader


class LoaderFactory:
    """
    Factory for creating appropriate data loaders based on file extension.
    
    Automatically detects the file type and returns the corresponding
    loader instance. Supports registration of custom loaders.
    
    Example:
        >>> # Automatic loader selection
        >>> df = LoaderFactory.load("data/users.csv")
        
        >>> # Get loader instance for more control
        >>> loader = LoaderFactory.get_loader("data/report.xlsx")
        >>> sheets = loader.get_sheet_names()
    """
    
    # Mapping of file extensions to loader classes
    _LOADERS: Dict[str, Type[BaseLoader]] = {
        ".csv": CSVLoader,
        ".tsv": CSVLoader,
        ".txt": CSVLoader,
        ".xlsx": ExcelLoader,
        ".xls": ExcelLoader,
        ".xlsm": ExcelLoader,
        ".xlsb": ExcelLoader,
        ".json": JSONLoader,
        ".jsonl": JSONLoader,
        ".pdf": PDFLoader,
    }
    
    @classmethod
    def get_supported_extensions(cls) -> list:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported extensions (e.g., ['.csv', '.xlsx', ...])
        """
        return list(cls._LOADERS.keys())
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        Check if a file type is supported.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            True if the file type is supported, False otherwise.
        """
        extension = Path(file_path).suffix.lower()
        return extension in cls._LOADERS
    
    @classmethod
    def get_loader(
        cls,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> BaseLoader:
        """
        Get the appropriate loader instance for a file.
        
        Args:
            file_path: Path to the data file.
            options: Optional loader-specific configuration.
        
        Returns:
            Appropriate loader instance for the file type.
        
        Raises:
            ValueError: If the file type is not supported.
        """
        extension = Path(file_path).suffix.lower()
        
        if extension not in cls._LOADERS:
            supported = ", ".join(cls._LOADERS.keys())
            raise ValueError(
                f"Unsupported file type '{extension}'. "
                f"Supported formats: {supported}"
            )
        
        loader_class = cls._LOADERS[extension]
        return loader_class(file_path, options)
    
    @classmethod
    def load(
        cls,
        file_path: str,
        options: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Load data from any supported file format.
        
        Convenience method that creates the appropriate loader
        and immediately loads the data.
        
        Args:
            file_path: Path to the data file.
            options: Optional loader-specific configuration.
        
        Returns:
            pd.DataFrame: The loaded data.
        
        Raises:
            ValueError: If the file type is not supported.
            FileNotFoundError: If the file does not exist.
        """
        loader = cls.get_loader(file_path, options)
        return loader.load()
    
    @classmethod
    def register_loader(
        cls,
        extension: str,
        loader_class: Type[BaseLoader]
    ) -> None:
        """
        Register a custom loader for a file extension.
        
        Args:
            extension: File extension (including dot, e.g., '.xml')
            loader_class: Loader class that inherits from BaseLoader
        
        Raises:
            TypeError: If loader_class doesn't inherit from BaseLoader.
        """
        if not issubclass(loader_class, BaseLoader):
            raise TypeError(
                f"Loader class must inherit from BaseLoader, "
                f"got {loader_class.__name__}"
            )
        
        # Normalize extension
        if not extension.startswith("."):
            extension = f".{extension}"
        
        cls._LOADERS[extension.lower()] = loader_class
    
    @classmethod
    def detect_file_type(cls, file_path: str) -> str:
        """
        Detect and return the file type category.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            File type category: 'csv', 'excel', 'json', 'pdf', or 'unknown'
        """
        extension = Path(file_path).suffix.lower()
        
        type_mapping = {
            **{ext: "csv" for ext in [".csv", ".tsv", ".txt"]},
            **{ext: "excel" for ext in [".xlsx", ".xls", ".xlsm", ".xlsb"]},
            **{ext: "json" for ext in [".json", ".jsonl"]},
            ".pdf": "pdf",
        }
        
        return type_mapping.get(extension, "unknown")
    
    @classmethod
    def get_loader_info(cls, file_path: str) -> Dict[str, Any]:
        """
        Get information about the loader that would be used for a file.
        
        Args:
            file_path: Path to the file.
        
        Returns:
            Dictionary with loader information.
        """
        extension = Path(file_path).suffix.lower()
        
        if extension in cls._LOADERS:
            loader_class = cls._LOADERS[extension]
            return {
                "extension": extension,
                "file_type": cls.detect_file_type(file_path),
                "loader_class": loader_class.__name__,
                "supported_extensions": loader_class.SUPPORTED_EXTENSIONS,
                "is_supported": True,
            }
        
        return {
            "extension": extension,
            "file_type": "unknown",
            "loader_class": None,
            "is_supported": False,
            "supported_formats": cls.get_supported_extensions(),
        }
