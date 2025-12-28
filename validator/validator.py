"""
Universal Validator Module

Core validation engine that applies Pydantic schemas to pandas DataFrames.
Handles row-by-row validation, error collection, and result aggregation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Type, Optional, Tuple
import json

import pandas as pd
import numpy as np
from pydantic import BaseModel, ValidationError as PydanticValidationError


@dataclass
class ValidationError:
    """
    Represents a single validation error.
    
    Attributes:
        row_index: Original index of the row in the DataFrame.
        column: Column name where the error occurred.
        error_type: Type of validation error (e.g., 'type_error', 'value_error')
        message: Human-readable error message.
        value: The invalid value that caused the error.
    """
    row_index: int
    column: str
    error_type: str
    message: str
    value: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "row_index": self.row_index,
            "column": self.column,
            "error_type": self.error_type,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None,
        }
    
    def __str__(self) -> str:
        return f"Row {self.row_index}, Column '{self.column}': {self.message}"


@dataclass
class ValidationResult:
    """
    Complete validation result containing valid/invalid data and error details.
    
    Attributes:
        valid_df: DataFrame containing rows that passed validation.
        invalid_df: DataFrame containing rows that failed validation.
        errors: List of ValidationError objects detailing each failure.
        total_rows: Total number of rows processed.
        valid_count: Number of rows that passed validation.
        invalid_count: Number of rows that failed validation.
        validation_time: Time taken for validation in seconds.
        schema_name: Name of the schema used for validation.
    """
    valid_df: pd.DataFrame
    invalid_df: pd.DataFrame
    errors: List[ValidationError]
    total_rows: int
    valid_count: int
    invalid_count: int
    validation_time: float
    schema_name: str
    
    @property
    def success_rate(self) -> float:
        """Calculate the percentage of valid rows."""
        if self.total_rows == 0:
            return 0.0
        return (self.valid_count / self.total_rows) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate the percentage of invalid rows."""
        return 100.0 - self.success_rate
    
    def get_errors_by_column(self) -> Dict[str, List[ValidationError]]:
        """Group errors by column name."""
        errors_by_col: Dict[str, List[ValidationError]] = {}
        for error in self.errors:
            if error.column not in errors_by_col:
                errors_by_col[error.column] = []
            errors_by_col[error.column].append(error)
        return errors_by_col
    
    def get_error_counts_by_column(self) -> Dict[str, int]:
        """Get count of errors per column."""
        counts: Dict[str, int] = {}
        for error in self.errors:
            counts[error.column] = counts.get(error.column, 0) + 1
        return counts
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of validation errors."""
        return {
            "total_errors": len(self.errors),
            "errors_by_column": self.get_error_counts_by_column(),
            "most_common_error_types": self._get_error_type_counts(),
        }
    
    def _get_error_type_counts(self) -> Dict[str, int]:
        """Count occurrences of each error type."""
        counts: Dict[str, int] = {}
        for error in self.errors:
            counts[error.error_type] = counts.get(error.error_type, 0) + 1
        return counts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format for JSON serialization."""
        return {
            "summary": {
                "schema_name": self.schema_name,
                "total_rows": self.total_rows,
                "valid_rows": self.valid_count,
                "invalid_rows": self.invalid_count,
                "success_rate": round(self.success_rate, 2),
                "error_rate": round(self.error_rate, 2),
                "validation_time_seconds": round(self.validation_time, 4),
            },
            "errors": [e.to_dict() for e in self.errors],
            "error_summary": self.get_error_summary(),
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class UniversalValidator:
    """
    Universal data validator that applies Pydantic schemas to DataFrames.
    
    This is the core validation engine of UniSchema. It takes a pandas DataFrame
    and validates each row against a specified Pydantic schema, collecting
    detailed error information for invalid rows.
    
    Example:
        >>> from unischema.schema import UserSchema
        >>> from unischema.loaders import LoaderFactory
        >>> 
        >>> # Load data
        >>> df = LoaderFactory.load("users.csv")
        >>> 
        >>> # Create validator
        >>> validator = UniversalValidator(UserSchema)
        >>> 
        >>> # Validate
        >>> result = validator.validate(df)
        >>> 
        >>> print(f"Valid rows: {result.valid_count}")
        >>> print(f"Invalid rows: {result.invalid_count}")
        >>> 
        >>> # Access clean data
        >>> clean_df = result.valid_df
    """
    
    def __init__(
        self,
        schema: Type[BaseModel],
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the validator with a Pydantic schema.
        
        Args:
            schema: Pydantic model class to use for validation.
            column_mapping: Optional mapping of DataFrame columns to schema fields.
                           Keys are DataFrame column names, values are schema field names.
        
        Example:
            >>> # Map 'user_id' column to 'id' field
            >>> validator = UniversalValidator(
            ...     UserSchema,
            ...     column_mapping={"user_id": "id", "full_name": "name"}
            ... )
        """
        self.schema = schema
        self.schema_name = schema.__name__
        self.column_mapping = column_mapping or {}
        self._schema_fields = set(schema.model_fields.keys())
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply column mapping to DataFrame.
        
        Args:
            df: Original DataFrame.
        
        Returns:
            DataFrame with renamed columns.
        """
        if not self.column_mapping:
            return df
        
        return df.rename(columns=self.column_mapping)
    
    def _prepare_row(self, row: pd.Series) -> Dict[str, Any]:
        """
        Prepare a DataFrame row for validation.
        
        Handles NaN values and type conversions.
        
        Args:
            row: pandas Series representing a single row.
        
        Returns:
            Dictionary suitable for Pydantic validation.
        """
        data: Dict[str, Any] = {}
        
        for key, value in row.items():
            # Skip columns not in schema
            if key not in self._schema_fields:
                continue
            
            # Handle NaN/None values
            if pd.isna(value):
                data[key] = None
            # Handle numpy types
            elif isinstance(value, np.integer):
                data[key] = int(value)
            elif isinstance(value, np.floating):
                data[key] = float(value)
            elif isinstance(value, np.bool_):
                data[key] = bool(value)
            else:
                data[key] = value
        
        return data
    
    def _parse_pydantic_errors(
        self,
        error: PydanticValidationError,
        row_index: int,
        row_data: Dict[str, Any]
    ) -> List[ValidationError]:
        """
        Parse Pydantic validation errors into our format.
        
        Args:
            error: Pydantic ValidationError exception.
            row_index: Index of the row that failed.
            row_data: Original row data for error context.
        
        Returns:
            List of ValidationError objects.
        """
        validation_errors: List[ValidationError] = []
        
        for err in error.errors():
            # Get field name from location
            location = err.get("loc", ())
            column = str(location[0]) if location else "unknown"
            
            # Get error type
            error_type = err.get("type", "unknown")
            
            # Get message
            message = err.get("msg", "Validation failed")
            
            # Get original value
            value = row_data.get(column)
            
            validation_errors.append(
                ValidationError(
                    row_index=row_index,
                    column=column,
                    error_type=error_type,
                    message=message,
                    value=value,
                )
            )
        
        return validation_errors
    
    def validate(
        self,
        df: pd.DataFrame,
        stop_on_first_error: bool = False
    ) -> ValidationResult:
        """
        Validate a DataFrame against the schema.
        
        Processes each row individually and collects validation results.
        
        Args:
            df: pandas DataFrame to validate.
            stop_on_first_error: If True, stop validation after first error (optional).
        
        Returns:
            ValidationResult containing valid/invalid DataFrames and error details.
        
        Example:
            >>> result = validator.validate(df)
            >>> print(f"Success rate: {result.success_rate:.1f}%")
            >>> 
            >>> # Get valid data for further processing
            >>> clean_data = result.valid_df
            >>> 
            >>> # Review errors
            >>> for error in result.errors[:5]:
            ...     print(error)
        """
        start_time = datetime.now()
        
        # Apply column mapping
        working_df = self._map_columns(df.copy())
        
        valid_indices: List[int] = []
        invalid_indices: List[int] = []
        all_errors: List[ValidationError] = []
        
        # Validate each row
        for idx in range(len(working_df)):
            row = working_df.iloc[idx]
            row_data = self._prepare_row(row)
            
            # Get original index for error reporting
            original_index = df.index[idx] if hasattr(df.index, '__getitem__') else idx
            
            try:
                # Attempt validation
                self.schema(**row_data)
                valid_indices.append(idx)
                
            except PydanticValidationError as e:
                invalid_indices.append(idx)
                errors = self._parse_pydantic_errors(e, original_index, row_data)
                all_errors.extend(errors)
                
                if stop_on_first_error:
                    break
        
        # Split DataFrame
        valid_df = df.iloc[valid_indices].copy() if valid_indices else pd.DataFrame()
        invalid_df = df.iloc[invalid_indices].copy() if invalid_indices else pd.DataFrame()
        
        # Calculate timing
        validation_time = (datetime.now() - start_time).total_seconds()
        
        return ValidationResult(
            valid_df=valid_df,
            invalid_df=invalid_df,
            errors=all_errors,
            total_rows=len(df),
            valid_count=len(valid_indices),
            invalid_count=len(invalid_indices),
            validation_time=validation_time,
            schema_name=self.schema_name,
        )
    
    def validate_single(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Validate a single record.
        
        Args:
            data: Dictionary of field values to validate.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            self.schema(**data)
            return True, []
        except PydanticValidationError as e:
            errors = self._parse_pydantic_errors(e, 0, data)
            return False, errors
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the validation schema.
        
        Returns:
            Dictionary with schema field information.
        """
        fields_info = {}
        
        for field_name, field_info in self.schema.model_fields.items():
            fields_info[field_name] = {
                "type": str(field_info.annotation),
                "required": field_info.is_required(),
                "description": field_info.description,
            }
        
        return {
            "schema_name": self.schema_name,
            "fields": fields_info,
            "required_fields": [
                name for name, info in fields_info.items() 
                if info["required"]
            ],
            "optional_fields": [
                name for name, info in fields_info.items() 
                if not info["required"]
            ],
        }
    
    def check_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check if DataFrame has required columns for validation.
        
        Args:
            df: DataFrame to check.
        
        Returns:
            Dictionary with column compatibility information.
        """
        df_columns = set(df.columns)
        
        # Apply mapping
        if self.column_mapping:
            mapped_cols = set()
            for col in df_columns:
                mapped_cols.add(self.column_mapping.get(col, col))
            df_columns = mapped_cols
        
        required_fields = {
            name for name, info in self.schema.model_fields.items()
            if info.is_required()
        }
        
        missing_required = required_fields - df_columns
        extra_columns = df_columns - self._schema_fields
        matched_columns = df_columns & self._schema_fields
        
        return {
            "compatible": len(missing_required) == 0,
            "missing_required": list(missing_required),
            "matched_columns": list(matched_columns),
            "extra_columns": list(extra_columns),
            "schema_fields": list(self._schema_fields),
        }
