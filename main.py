#!/usr/bin/env python3
"""
UniSchema – Universal Data Validation & Quality Analysis Engine

Main module providing programmatic access to the validation engine.
Use this for integration into Python applications or scripts.

Example:
    >>> from unischema.main import validate_file
    >>> 
    >>> result = validate_file(
    ...     file_path="data/users.csv",
    ...     schema_name="user",
    ...     output_dir="outputs/"
    ... )
    >>> 
    >>> print(f"Valid rows: {result['valid_count']}")
"""

import sys
import types
from pathlib import Path
from typing import Dict, Any, Optional, Type, Union

import pandas as pd
from pydantic import BaseModel

# Register 'unischema' module shim if running directly
root_dir = str(Path(__file__).resolve().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if "unischema" not in sys.modules:
    mod = types.ModuleType("unischema")
    mod.__path__ = [root_dir]
    mod.__file__ = str(Path(root_dir) / "__init__.py")
    sys.modules["unischema"] = mod

try:
    from .loaders import LoaderFactory
    from .schema.user_schema import UserSchema, EmployeeSchema
    from .validator import UniversalValidator, ValidationResult
    from .analysis import DataQualityMetrics, ValidationSummary
    from .visualize import ReportGenerator
except (ImportError, ValueError):
    from unischema.loaders import LoaderFactory
    from unischema.schema.user_schema import UserSchema, EmployeeSchema
    from unischema.validator import UniversalValidator, ValidationResult
    from unischema.analysis import DataQualityMetrics, ValidationSummary
    from unischema.visualize import ReportGenerator


# Default schema registry
SCHEMAS = {
    "user": UserSchema,
    "employee": EmployeeSchema,
}


def load_data(file_path: str, options: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Load data from any supported file format.
    
    Args:
        file_path: Path to the data file.
        options: Optional loader-specific configuration.
    
    Returns:
        pandas DataFrame with the loaded data.
    
    Raises:
        ValueError: If file format is not supported.
        FileNotFoundError: If file doesn't exist.
    
    Example:
        >>> df = load_data("data/users.csv")
        >>> df = load_data("data/report.xlsx", options={"sheet_name": "Data"})
    """
    return LoaderFactory.load(file_path, options)


def validate_dataframe(
    df: pd.DataFrame,
    schema: Union[Type[BaseModel], str],
    column_mapping: Optional[Dict[str, str]] = None
) -> ValidationResult:
    """
    Validate a DataFrame against a Pydantic schema.
    
    Args:
        df: pandas DataFrame to validate.
        schema: Pydantic model class or schema name string.
        column_mapping: Optional mapping of DataFrame columns to schema fields.
    
    Returns:
        ValidationResult with valid/invalid data and error details.
    
    Example:
        >>> from unischema.schema import UserSchema
        >>> result = validate_dataframe(df, UserSchema)
        >>> print(f"Success rate: {result.success_rate:.1f}%")
    """
    # Resolve schema if string
    if isinstance(schema, str):
        schema_name = schema.lower()
        if schema_name not in SCHEMAS:
            raise ValueError(f"Unknown schema: {schema}. Available: {list(SCHEMAS.keys())}")
        schema = SCHEMAS[schema_name]
    
    validator = UniversalValidator(schema, column_mapping)
    return validator.validate(df)


def analyze_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform data quality analysis on a DataFrame.
    
    Args:
        df: pandas DataFrame to analyze.
    
    Returns:
        Dictionary with comprehensive quality metrics.
    
    Example:
        >>> metrics = analyze_quality(df)
        >>> print(f"Completeness: {metrics['completeness_score']}%")
    """
    metrics = DataQualityMetrics(df)
    return metrics.compute_all()


def generate_reports(
    validation_result: ValidationResult,
    original_df: pd.DataFrame,
    output_dir: str,
    source_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate all reports and visualizations.
    
    Args:
        validation_result: Result from validation.
        original_df: Original DataFrame.
        output_dir: Directory to save outputs.
        source_file: Optional source file path for metadata.
    
    Returns:
        Dictionary with paths to all generated files.
    
    Example:
        >>> outputs = generate_reports(result, df, "outputs/")
        >>> print(f"Generated plots: {outputs['error_plots']}")
    """
    generator = ReportGenerator(
        validation_result=validation_result,
        original_df=original_df,
        source_file=source_file
    )
    return generator.generate_all(output_dir)


def validate_file(
    file_path: str,
    schema_name: str = "user",
    output_dir: Optional[str] = None,
    loader_options: Optional[Dict[str, Any]] = None,
    column_mapping: Optional[Dict[str, str]] = None,
    print_summary: bool = True
) -> Dict[str, Any]:
    """
    Complete validation workflow for a data file.
    
    This is the main entry point for validating files. It:
    1. Loads data from the file
    2. Validates against the specified schema
    3. Computes quality metrics
    4. Optionally generates reports and plots
    
    Args:
        file_path: Path to the data file.
        schema_name: Name of the schema to use ('user' or 'employee').
        output_dir: Optional directory to save reports and plots.
        loader_options: Optional loader-specific configuration.
        column_mapping: Optional column name mapping.
        print_summary: Whether to print summary to terminal.
    
    Returns:
        Dictionary with validation results and outputs.
    
    Example:
        >>> result = validate_file(
        ...     file_path="data/users.csv",
        ...     schema_name="user",
        ...     output_dir="outputs/",
        ...     print_summary=True
        ... )
        >>> 
        >>> if result["valid_count"] == result["total_rows"]:
        ...     print("All data is valid!")
    """
    # Verify file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get schema
    schema_name_lower = schema_name.lower()
    if schema_name_lower not in SCHEMAS:
        raise ValueError(
            f"Unknown schema: {schema_name}. "
            f"Available: {list(SCHEMAS.keys())}"
        )
    schema = SCHEMAS[schema_name_lower]
    
    # Load data
    df = load_data(file_path, loader_options)
    
    # Validate
    result = validate_dataframe(df, schema, column_mapping)
    
    # Compute quality metrics
    quality_metrics = analyze_quality(df)
    
    # Create summary
    summary = ValidationSummary(result, df, file_path)
    
    # Print summary if requested
    if print_summary:
        print(summary.get_terminal_summary())
    
    # Prepare base output
    output = {
        "file_path": file_path,
        "schema_name": schema.__name__,
        "total_rows": result.total_rows,
        "valid_count": result.valid_count,
        "invalid_count": result.invalid_count,
        "success_rate": result.success_rate,
        "error_rate": result.error_rate,
        "validation_time": result.validation_time,
        "quality_metrics": quality_metrics,
        "validation_result": result,
        "original_df": df,
        "outputs": None,
    }
    
    # Generate reports if output directory specified
    if output_dir:
        outputs = generate_reports(result, df, output_dir, file_path)
        output["outputs"] = outputs
    
    return output


def get_supported_formats() -> list:
    """
    Get list of supported file formats.
    
    Returns:
        List of supported file extensions.
    """
    return LoaderFactory.get_supported_extensions()


def get_available_schemas() -> Dict[str, Type[BaseModel]]:
    """
    Get dictionary of available schemas.
    
    Returns:
        Dictionary mapping schema names to classes.
    """
    return SCHEMAS.copy()


def register_schema(name: str, schema: Type[BaseModel]) -> None:
    """
    Register a custom schema.
    
    Args:
        name: Name to register the schema under.
        schema: Pydantic model class.
    
    Example:
        >>> from pydantic import BaseModel, Field
        >>> 
        >>> class ProductSchema(BaseModel):
        ...     id: int = Field(gt=0)
        ...     name: str
        ...     price: float = Field(gt=0)
        >>> 
        >>> register_schema("product", ProductSchema)
    """
    if not issubclass(schema, BaseModel):
        raise TypeError("Schema must be a Pydantic BaseModel subclass")
    
    SCHEMAS[name.lower()] = schema


# Convenience alias for CLI
def main() -> None:
    """Entry point for the CLI."""
    try:
        from .cli import main as cli_main
    except (ImportError, ValueError):
        from unischema.cli import main as cli_main
    import sys
    sys.exit(cli_main())


if __name__ == "__main__":
    main()
