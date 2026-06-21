"""
Data Quality Metrics Module

Computes comprehensive data quality metrics using pandas and numpy.
Provides insights into data completeness, uniqueness, and distribution.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import json

import pandas as pd
import numpy as np


@dataclass
class ColumnMetrics:
    """Metrics for a single column."""
    column_name: str
    dtype: str
    total_count: int
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    # Numeric-specific metrics
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    # String-specific metrics
    avg_length: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "column_name": self.column_name,
            "dtype": self.dtype,
            "total_count": self.total_count,
            "non_null_count": self.non_null_count,
            "null_count": self.null_count,
            "null_percentage": round(self.null_percentage, 2),
            "unique_count": self.unique_count,
            "unique_percentage": round(self.unique_percentage, 2),
        }
        
        # Add numeric metrics if present
        if self.mean is not None:
            result.update({
                "mean": round(self.mean, 4) if self.mean else None,
                "median": round(self.median, 4) if self.median else None,
                "std": round(self.std, 4) if self.std else None,
                "min": self.min_value,
                "max": self.max_value,
                "q25": self.q25,
                "q75": self.q75,
            })
        
        # Add string metrics if present
        if self.avg_length is not None:
            result.update({
                "avg_length": round(self.avg_length, 2),
                "min_length": self.min_length,
                "max_length": self.max_length,
            })
        
        return result


class DataQualityMetrics:
    """
    Computes data quality metrics for a pandas DataFrame.
    
    Analyzes data completeness, uniqueness, distributions, and basic
    statistics using pandas and numpy.
    
    Example:
        >>> metrics = DataQualityMetrics(df)
        >>> report = metrics.compute_all()
        >>> print(f"Completeness: {report['completeness_score']:.1f}%")
        >>> 
        >>> # Get column-specific metrics
        >>> col_metrics = metrics.get_column_metrics("email")
        >>> print(f"Missing emails: {col_metrics.null_percentage:.1f}%")
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize metrics calculator with a DataFrame.
        
        Args:
            df: pandas DataFrame to analyze.
        """
        self.df = df
        self._column_metrics: Dict[str, ColumnMetrics] = {}
    
    @property
    def total_rows(self) -> int:
        """Total number of rows in the DataFrame."""
        return len(self.df)
    
    @property
    def total_columns(self) -> int:
        """Total number of columns in the DataFrame."""
        return len(self.df.columns)
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """
        Get basic DataFrame statistics.
        
        Returns:
            Dictionary with row/column counts and memory usage.
        """
        return {
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "memory_usage_bytes": int(self.df.memory_usage(deep=True).sum()),
            "memory_usage_mb": round(
                self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2
            ),
        }
    
    def get_missing_values(self) -> Dict[str, Any]:
        """
        Analyze missing values across all columns.
        
        Returns:
            Dictionary with missing value statistics.
        """
        null_counts = self.df.isnull().sum()
        null_percentages = (null_counts / self.total_rows) * 100
        
        missing_by_column = {
            col: {
                "count": int(null_counts[col]),
                "percentage": round(float(null_percentages[col]), 2)
            }
            for col in self.df.columns
        }
        
        total_missing = int(null_counts.sum())
        total_cells = self.total_rows * self.total_columns
        
        return {
            "total_missing_values": total_missing,
            "total_cells": total_cells,
            "overall_missing_percentage": round(
                (total_missing / total_cells) * 100 if total_cells > 0 else 0, 2
            ),
            "columns_with_missing": sum(null_counts > 0),
            "complete_columns": sum(null_counts == 0),
            "missing_by_column": missing_by_column,
        }
    
    def get_duplicate_stats(self) -> Dict[str, Any]:
        """
        Analyze duplicate rows in the DataFrame.
        
        Returns:
            Dictionary with duplicate row statistics.
        """
        duplicate_mask = self.df.duplicated()
        duplicate_count = int(duplicate_mask.sum())
        
        # Find which rows are duplicates
        duplicate_indices = list(self.df[duplicate_mask].index)
        
        return {
            "total_rows": self.total_rows,
            "duplicate_rows": duplicate_count,
            "unique_rows": self.total_rows - duplicate_count,
            "duplicate_percentage": round(
                (duplicate_count / self.total_rows) * 100 if self.total_rows > 0 else 0, 2
            ),
            "duplicate_indices": duplicate_indices[:100],  # Limit to first 100
        }
    
    def get_column_metrics(self, column: str) -> ColumnMetrics:
        """
        Get detailed metrics for a specific column.
        
        Args:
            column: Column name to analyze.
        
        Returns:
            ColumnMetrics object with detailed statistics.
        
        Raises:
            KeyError: If column doesn't exist in DataFrame.
        """
        if column not in self.df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame")
        
        if column in self._column_metrics:
            return self._column_metrics[column]
        
        series = self.df[column]
        total = len(series)
        non_null = series.notna().sum()
        null = series.isna().sum()
        unique = series.nunique()
        
        metrics = ColumnMetrics(
            column_name=column,
            dtype=str(series.dtype),
            total_count=total,
            non_null_count=int(non_null),
            null_count=int(null),
            null_percentage=(null / total) * 100 if total > 0 else 0,
            unique_count=int(unique),
            unique_percentage=(unique / non_null) * 100 if non_null > 0 else 0,
        )
        
        # Add numeric metrics if applicable (exclude boolean)
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            valid_series = series.dropna()
            if len(valid_series) > 0:
                try:
                    metrics.mean = float(np.mean(valid_series))
                    metrics.median = float(np.median(valid_series))
                    metrics.std = float(np.std(valid_series))
                    metrics.min_value = float(np.min(valid_series))
                    metrics.max_value = float(np.max(valid_series))
                    metrics.q25 = float(np.percentile(valid_series, 25))
                    metrics.q75 = float(np.percentile(valid_series, 75))
                except (TypeError, ValueError):
                    pass  # Skip if numeric operations fail
        
        # Add string metrics if applicable
        elif pd.api.types.is_string_dtype(series) or series.dtype == object:
            str_series = series.dropna().astype(str)
            if len(str_series) > 0:
                lengths = str_series.str.len()
                metrics.avg_length = float(lengths.mean())
                metrics.min_length = int(lengths.min())
                metrics.max_length = int(lengths.max())
        
        self._column_metrics[column] = metrics
        return metrics
    
    def get_all_column_metrics(self) -> Dict[str, ColumnMetrics]:
        """
        Get metrics for all columns.
        
        Returns:
            Dictionary mapping column names to ColumnMetrics objects.
        """
        for col in self.df.columns:
            self.get_column_metrics(col)
        return self._column_metrics
    
    def get_numeric_summary(self) -> pd.DataFrame:
        """
        Get statistical summary for numeric columns.
        
        Returns:
            DataFrame with descriptive statistics.
        """
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return pd.DataFrame()
        return numeric_df.describe()
    
    def get_data_types(self) -> Dict[str, str]:
        """
        Get data types for all columns.
        
        Returns:
            Dictionary mapping column names to their data types.
        """
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}
    
    def compute_completeness_score(self) -> float:
        """
        Compute overall data completeness score (0-100).
        
        Returns:
            Completeness percentage based on non-null values.
        """
        total_cells = self.total_rows * self.total_columns
        if total_cells == 0:
            return 0.0
        
        filled_cells = total_cells - self.df.isnull().sum().sum()
        return (filled_cells / total_cells) * 100
    
    def compute_all(self) -> Dict[str, Any]:
        """
        Compute all data quality metrics.
        
        Returns:
            Comprehensive dictionary with all metrics.
        """
        return {
            "basic_stats": self.get_basic_stats(),
            "missing_values": self.get_missing_values(),
            "duplicate_stats": self.get_duplicate_stats(),
            "data_types": self.get_data_types(),
            "completeness_score": round(self.compute_completeness_score(), 2),
            "column_metrics": {
                col: self.get_column_metrics(col).to_dict()
                for col in self.df.columns
            },
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Export all metrics as JSON.
        
        Args:
            indent: JSON indentation level.
        
        Returns:
            JSON string with all metrics.
        """
        return json.dumps(self.compute_all(), indent=indent, default=str)
    
    def get_data_quality_issues(self) -> List[Dict[str, Any]]:
        """
        Identify potential data quality issues.
        
        Returns:
            List of identified issues with descriptions.
        """
        issues = []
        
        # Check for high missing value rates
        missing = self.get_missing_values()
        for col, stats in missing["missing_by_column"].items():
            if stats["percentage"] > 50:
                issues.append({
                    "type": "high_missing_rate",
                    "severity": "high",
                    "column": col,
                    "description": f"Column '{col}' has {stats['percentage']}% missing values"
                })
            elif stats["percentage"] > 20:
                issues.append({
                    "type": "moderate_missing_rate",
                    "severity": "medium",
                    "column": col,
                    "description": f"Column '{col}' has {stats['percentage']}% missing values"
                })
        
        # Check for duplicates
        dup_stats = self.get_duplicate_stats()
        if dup_stats["duplicate_percentage"] > 10:
            issues.append({
                "type": "high_duplicate_rate",
                "severity": "high",
                "column": None,
                "description": f"Dataset has {dup_stats['duplicate_percentage']}% duplicate rows"
            })
        
        # Check for low uniqueness
        for col in self.df.columns:
            metrics = self.get_column_metrics(col)
            if metrics.unique_count == 1 and metrics.non_null_count > 1:
                issues.append({
                    "type": "single_value_column",
                    "severity": "low",
                    "column": col,
                    "description": f"Column '{col}' contains only a single unique value"
                })
        
        return issues
