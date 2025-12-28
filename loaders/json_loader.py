"""
JSON Loader Module

Handles loading data from JSON files.
Supports both flat JSON arrays and nested JSON structures.
Nested structures are automatically flattened for tabular representation.
"""

import json
from typing import Optional, Dict, Any, List, Union

import pandas as pd

from .base_loader import BaseLoader


class JSONLoader(BaseLoader):
    """
    Loader for JSON files.
    
    Supports:
    - Flat JSON arrays (list of objects)
    - Nested JSON structures (automatically flattened)
    - JSON Lines format (.jsonl)
    
    Example:
        >>> loader = JSONLoader("data/users.json")
        >>> df = loader.load()
        >>> print(df.head())
        
        >>> # Load with custom flattening depth
        >>> loader = JSONLoader("data/nested.json", options={"max_depth": 3})
        >>> df = loader.load()
    """
    
    SUPPORTED_EXTENSIONS = (".json", ".jsonl")
    
    DEFAULT_OPTIONS: Dict[str, Any] = {
        "encoding": "utf-8",
        "flatten": True,
        "max_depth": 10,
        "separator": ".",
    }
    
    def __init__(self, file_path: str, options: Optional[Dict[str, Any]] = None):
        """
        Initialize the JSON loader.
        
        Args:
            file_path: Path to the JSON file.
            options: Optional dictionary of options.
                     - encoding: File encoding (default: utf-8)
                     - flatten: Whether to flatten nested structures (default: True)
                     - max_depth: Maximum nesting depth to flatten (default: 10)
                     - separator: Key separator for flattened fields (default: .)
        """
        super().__init__(file_path, options)
        self._merge_default_options()
    
    def _merge_default_options(self) -> None:
        """Merge user options with defaults."""
        merged = self.DEFAULT_OPTIONS.copy()
        merged.update(self.options)
        self.options = merged
    
    def _flatten_dict(
        self,
        data: Dict[str, Any],
        parent_key: str = "",
        separator: str = ".",
        depth: int = 0,
        max_depth: int = 10,
    ) -> Dict[str, Any]:
        """
        Flatten a nested dictionary into a single-level dictionary.
        
        Args:
            data: Dictionary to flatten.
            parent_key: Prefix for nested keys.
            separator: Separator between parent and child keys.
            depth: Current nesting depth.
            max_depth: Maximum depth to flatten.
        
        Returns:
            Flattened dictionary.
        """
        items: List[tuple] = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            if isinstance(value, dict) and depth < max_depth:
                items.extend(
                    self._flatten_dict(
                        value,
                        new_key,
                        separator,
                        depth + 1,
                        max_depth,
                    ).items()
                )
            elif isinstance(value, list):
                # Handle lists: convert to string or expand if simple
                if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                    items.append((new_key, value))
                else:
                    # Complex nested lists - convert to JSON string
                    items.append((new_key, json.dumps(value)))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    def _flatten_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Flatten a list of records.
        
        Args:
            records: List of dictionaries to flatten.
        
        Returns:
            List of flattened dictionaries.
        """
        separator = self.options.get("separator", ".")
        max_depth = self.options.get("max_depth", 10)
        
        return [
            self._flatten_dict(record, separator=separator, max_depth=max_depth)
            for record in records
        ]
    
    def _load_jsonl(self) -> List[Dict[str, Any]]:
        """
        Load JSON Lines format file.
        
        Returns:
            List of parsed JSON objects.
        """
        records = []
        encoding = self.options.get("encoding", "utf-8")
        
        with open(self.file_path, "r", encoding=encoding) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON at line {line_num}: {str(e)}"
                    ) from e
        
        return records
    
    def _load_json(self) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Load standard JSON file.
        
        Returns:
            Parsed JSON data (list or dict).
        """
        encoding = self.options.get("encoding", "utf-8")
        
        with open(self.file_path, "r", encoding=encoding) as f:
            return json.load(f)
    
    def load(self) -> pd.DataFrame:
        """
        Load data from the JSON file into a pandas DataFrame.
        
        Automatically handles:
        - JSON arrays (list of objects)
        - Single JSON objects (converted to single-row DataFrame)
        - Nested structures (flattened if enabled)
        - JSON Lines format
        
        Returns:
            pd.DataFrame: The loaded and processed JSON data.
        
        Raises:
            ValueError: If the JSON structure cannot be converted to tabular format.
        """
        try:
            # Determine if JSONL format
            if self.file_path.suffix.lower() == ".jsonl":
                data = self._load_jsonl()
            else:
                data = self._load_json()
            
            # Normalize to list of records
            if isinstance(data, dict):
                # Check if it's a dict with a data key containing records
                if "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                elif "records" in data and isinstance(data["records"], list):
                    records = data["records"]
                elif "items" in data and isinstance(data["items"], list):
                    records = data["items"]
                else:
                    # Single object - wrap in list
                    records = [data]
            elif isinstance(data, list):
                records = data
            else:
                raise ValueError(
                    f"Unsupported JSON structure. Expected object or array, "
                    f"got {type(data).__name__}"
                )
            
            if not records:
                return pd.DataFrame()
            
            # Flatten if enabled
            if self.options.get("flatten", True):
                records = self._flatten_records(records)
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Clean column names
            df.columns = df.columns.astype(str).str.strip()
            
            return df
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in file '{self.file_path}': {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to load JSON file '{self.file_path}': {str(e)}"
            ) from e
    
    def get_structure_preview(self) -> Dict[str, Any]:
        """
        Get a preview of the JSON structure without loading all data.
        
        Returns:
            Dictionary with structure information.
        """
        try:
            if self.file_path.suffix.lower() == ".jsonl":
                data = self._load_jsonl()[:5]  # First 5 records
            else:
                data = self._load_json()
            
            return {
                "type": type(data).__name__,
                "record_count": len(data) if isinstance(data, list) else 1,
                "sample_keys": (
                    list(data[0].keys()) if isinstance(data, list) and data 
                    else list(data.keys()) if isinstance(data, dict)
                    else []
                ),
            }
        except Exception as e:
            return {"error": str(e)}
