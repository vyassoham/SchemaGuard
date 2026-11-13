#!/usr/bin/env python3
"""
UniSchema Demo Script

Demonstrates the core functionality of the UniSchema validation engine.
Run this script to see the validation workflow in action.

Usage:
    python demo.py
"""

import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path and register 'unischema' module shim
root_dir = str(Path(__file__).resolve().parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if "unischema" not in sys.modules:
    import types
    mod = types.ModuleType("unischema")
    mod.__path__ = [root_dir]
    mod.__file__ = str(Path(root_dir) / "__init__.py")
    sys.modules["unischema"] = mod

from unischema.loaders import LoaderFactory
from unischema.schema import UserSchema
from unischema.validator import UniversalValidator
from unischema.analysis import DataQualityMetrics, ValidationSummary
from unischema.visualize import ReportGenerator


def main():
    """Run the demonstration."""
    
    print("\n" + "=" * 70)
    print("   🔍 UniSchema – Universal Data Validation Engine Demo")
    print("=" * 70)
    
    # Define sample/test file path
    samples_dir = Path(__file__).parent / "samples"
    csv_file = samples_dir / "users.csv"
    
    # Check if sample file exists
    if not csv_file.exists():
        print(f"\n❌ Sample file not found: {csv_file}")
        print("   Please ensure the samples directory contains users.csv")
        return 1
    
    # Step 1: Load Data
    print("\n📁 STEP 1: Loading Data")
    print("-" * 50)
    
    df = LoaderFactory.load(str(csv_file))
    print(f"   Loaded file: {csv_file.name}")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {list(df.columns)}")
    
    # Step 2: Data Quality Analysis
    print("\n📊 STEP 2: Data Quality Analysis")
    print("-" * 50)
    
    metrics = DataQualityMetrics(df)
    quality = metrics.compute_all()
    
    print(f"   Completeness Score: {quality['completeness_score']:.1f}%")
    print(f"   Duplicate Rows: {quality['duplicate_stats']['duplicate_rows']}")
    
    missing = quality['missing_values']['missing_by_column']
    cols_with_missing = [col for col, info in missing.items() if info['count'] > 0]
    if cols_with_missing:
        print(f"   Columns with missing values: {cols_with_missing}")
    
    # Step 3: Schema Validation
    print("\n✅ STEP 3: Schema Validation")
    print("-" * 50)
    
    validator = UniversalValidator(UserSchema)
    result = validator.validate(df)
    
    print(f"   Schema: {UserSchema.__name__}")
    print(f"   Valid Rows: {result.valid_count} ({result.success_rate:.1f}%)")
    print(f"   Invalid Rows: {result.invalid_count} ({result.error_rate:.1f}%)")
    print(f"   Validation Time: {result.validation_time:.4f}s")
    
    # Show some errors
    if result.errors:
        print(f"\n   Sample Errors (first 5):")
        for error in result.errors[:5]:
            print(f"   - Row {error.row_index}, '{error.column}': {error.message}")
    
    # Step 4: Generate Reports
    print("\n📈 STEP 4: Generate Reports")
    print("-" * 50)
    
    output_dir = Path(__file__).parent / "outputs"
    
    generator = ReportGenerator(result, df, str(csv_file))
    outputs = generator.generate_all(str(output_dir))
    
    total_files = sum(
        len(files) if isinstance(files, list) else len(files)
        for files in outputs.values()
    )
    print(f"   Generated {total_files} output files in: {output_dir}")
    
    print("\n   Plots generated:")
    for plot_path in outputs.get("error_plots", []):
        print(f"   - {Path(plot_path).name}")
    for plot_path in outputs.get("missing_plots", []):
        print(f"   - {Path(plot_path).name}")
    for plot_path in outputs.get("distribution_plots", []):
        print(f"   - {Path(plot_path).name}")
    
    print("\n   Reports generated:")
    for name, path in outputs.get("reports", {}).items():
        print(f"   - {name}: {Path(path).name}")
    
    # Summary
    print("\n" + "=" * 70)
    print("   ✨ Demo Complete!")
    print("=" * 70)
    print(f"\n   Check the '{output_dir}' directory for generated files.")
    print("   You can explore the JSON report and PNG visualizations.\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
