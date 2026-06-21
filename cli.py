#!/usr/bin/env python3
"""
UniSchema CLI Module

Command-line interface for the UniSchema validation engine.
Provides easy access to validation, quality analysis, and report generation.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel

from .loaders import LoaderFactory
from .schema.user_schema import UserSchema, EmployeeSchema
from .validator import UniversalValidator
from .analysis import ValidationSummary
from .visualize import ReportGenerator


# Registry of available schemas
SCHEMA_REGISTRY = {
    "user": UserSchema,
    "users": UserSchema,
    "user_schema": UserSchema,
    "employee": EmployeeSchema,
    "employees": EmployeeSchema,
    "employee_schema": EmployeeSchema,
}


def get_schema_by_name(name: str) -> Type[BaseModel]:
    """
    Get a schema class by its name.
    
    Args:
        name: Schema name (e.g., 'user', 'employee')
    
    Returns:
        Schema class
    
    Raises:
        ValueError: If schema name is not recognized
    """
    name_lower = name.lower().replace("-", "_")
    
    if name_lower in SCHEMA_REGISTRY:
        return SCHEMA_REGISTRY[name_lower]
    
    # Try to interpret as module path
    if "." in name:
        try:
            module_path, class_name = name.rsplit(".", 1)
            import importlib
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except Exception as e:
            raise ValueError(f"Could not load schema from '{name}': {e}")
    
    available = ", ".join(set(SCHEMA_REGISTRY.keys()))
    raise ValueError(
        f"Unknown schema '{name}'. Available schemas: {available}\n"
        f"Or provide a full module path like 'mymodule.MySchema'"
    )


def cmd_check(args: argparse.Namespace) -> int:
    """Execute the 'check' command for validation."""
    
    print("\n" + "=" * 60)
    print("  UniSchema Validation Engine")
    print("=" * 60)
    
    file_path = args.file
    
    # Verify file exists
    if not Path(file_path).exists():
        print(f"\nError: File not found: {file_path}")
        return 1
    
    # Check if format is supported
    if not LoaderFactory.is_supported(file_path):
        supported = ", ".join(LoaderFactory.get_supported_extensions())
        print(f"\nError: Unsupported file format")
        print(f"   Supported formats: {supported}")
        return 1
    
    # Get schema
    try:
        schema_class = get_schema_by_name(args.schema)
        print(f"\nSchema: {schema_class.__name__}")
    except ValueError as e:
        print(f"\nError: {e}")
        return 1
    
    # Load data
    print(f"Loading: {file_path}")
    try:
        df = LoaderFactory.load(file_path)
        print(f"   Loaded {len(df):,} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"\nError loading file: {e}")
        return 1
    
    # Validate
    print("\nValidating data...")
    validator = UniversalValidator(schema_class)
    
    # Check column compatibility
    col_check = validator.check_columns(df)
    if not col_check["compatible"]:
        print(f"\nWarning: Missing required columns: {col_check['missing_required']}")
    
    result = validator.validate(df)
    
    # Create summary
    summary = ValidationSummary(result, df, file_path)
    
    # Print terminal summary
    print(summary.get_terminal_summary())
    
    # Save outputs if output directory specified
    if args.output:
        output_dir = args.output
        
        print(f"\nGenerating reports and plots...")
        
        # Generate all outputs
        generator = ReportGenerator(result, df, file_path)
        outputs = generator.generate_all(output_dir)
        
        print(generator.get_output_summary(outputs))
        print(f"   Outputs saved to: {output_dir}")
    
    # Return appropriate exit code
    if result.invalid_count > 0:
        return 2  # Validation found issues
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Execute the 'info' command for file information."""
    
    file_path = args.file
    
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return 1
    
    print("\n" + "=" * 50)
    print("  File Information")
    print("=" * 50)
    
    # Get loader info
    loader_info = LoaderFactory.get_loader_info(file_path)
    
    print(f"\n  File: {Path(file_path).name}")
    print(f"  Type: {loader_info['file_type']}")
    print(f"  Extension: {loader_info['extension']}")
    print(f"  Supported: {'Yes' if loader_info['is_supported'] else 'No'}")
    
    if loader_info["is_supported"]:
        print(f"  Loader: {loader_info['loader_class']}")
        
        # Load and show preview
        try:
            df = LoaderFactory.load(file_path)
            print(f"\n  Rows: {len(df):,}")
            print(f"  Columns: {len(df.columns)}")
            print(f"\n  Column Names:")
            for col in df.columns:
                dtype = df[col].dtype
                null_count = df[col].isnull().sum()
                print(f"    - {col} ({dtype}, {null_count} nulls)")
        except Exception as e:
            print(f"\n  Error loading preview: {e}")
    
    print("\n" + "=" * 50)
    
    return 0


def cmd_schemas(args: argparse.Namespace) -> int:
    """Execute the 'schemas' command to list available schemas."""
    
    print("\n" + "=" * 50)
    print("  Available Schemas")
    print("=" * 50)
    
    # Get unique schemas
    unique_schemas = {}
    for name, schema in SCHEMA_REGISTRY.items():
        if schema.__name__ not in unique_schemas:
            unique_schemas[schema.__name__] = schema
    
    for schema_name, schema_class in unique_schemas.items():
        print(f"\n  📋 {schema_name}")
        print("-" * 40)
        
        for field_name, field_info in schema_class.model_fields.items():
            required = "required" if field_info.is_required() else "optional"
            desc = field_info.description or ""
            print(f"    • {field_name} ({required})")
            if desc:
                print(f"      {desc}")
    
    print("\n" + "=" * 50)
    
    return 0


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI."""
    # Reconfigure stdout/stderr to UTF-8 to handle emojis safely on Windows
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
                
    parser = argparse.ArgumentParser(
        prog="unischema",
        description="UniSchema – Universal Data Validation & Quality Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a CSV file
  unischema check --file data.csv --schema user

  # Validate and save reports
  unischema check --file data.xlsx --schema employee --output ./outputs

  # Get file information
  unischema info --file data.json

  # List available schemas
  unischema schemas
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="UniSchema 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser(
        "check",
        help="Validate a data file against a schema"
    )
    check_parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to the data file (CSV, Excel, JSON, or PDF)"
    )
    check_parser.add_argument(
        "--schema", "-s",
        default="user",
        help="Schema to validate against (default: user)"
    )
    check_parser.add_argument(
        "--output", "-o",
        help="Output directory for reports and plots"
    )
    
    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Get information about a data file"
    )
    info_parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to the data file"
    )
    
    # Schemas command
    subparsers.add_parser(
        "schemas",
        help="List available schemas"
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Execute command
    if args.command == "check":
        return cmd_check(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "schemas":
        return cmd_schemas(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
