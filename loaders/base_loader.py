"""
Base Loader Module

Defines the abstract base class for all data loaders.
All file-specific loaders must inherit from BaseLoader and implement
the load() method to return a pandas DataFrame.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd


class BaseLoader(ABC):
    """
    Abstract base class for all data loaders.
    
    Each loader is responsible for reading a specific file format
    and converting it into a pandas DataFrame for unified processing.
    
    Attributes:
        file_path: Path to the file to be loaded.
        options: Optional configuration dictionary for loader-specific settings.
    """
    
    SUPPORTED_EXTENSIONS: tuple = ()
    
    def __init__(self, file_path: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the loader with a file path and optional configuration.
        
        Args:
            file_path: Path to the data file.
            options: Optional dictionary of loader-specific options.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file extension is not supported by this loader.
        """
        self.file_path = Path(file_path)
        self.options = options or {}
        
        self._validate_file_exists()
        self._validate_extension()
    
    def _validate_file_exists(self) -> None:
        """Verify that the file exists at the specified path."""
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"File not found: {self.file_path}"
            )
    
    def _validate_extension(self) -> None:
        """Verify that the file extension is supported by this loader."""
        if self.SUPPORTED_EXTENSIONS:
            extension = self.file_path.suffix.lower()
            if extension not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file extension '{extension}'. "
                    f"This loader supports: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                )
    
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """
        Load data from the file and return as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: The loaded data in tabular format.
        
        Raises:
            Exception: If the file cannot be loaded or parsed.
        """
        pass
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get metadata about the file.
        
        Returns:
            Dictionary containing file metadata.
        """
        return {
            "file_path": str(self.file_path.absolute()),
            "file_name": self.file_path.name,
            "extension": self.file_path.suffix.lower(),
            "size_bytes": self.file_path.stat().st_size if self.file_path.exists() else 0,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(file_path='{self.file_path}')"
