"""
Validation Summary Module

Generates comprehensive validation summary reports combining
validation results with data quality metrics.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

import pandas as pd

from ..validator.validator import ValidationResult
from .metrics import DataQualityMetrics


class ValidationSummary:
    """
    Generates comprehensive validation summary reports.
    
    Combines validation results with data quality metrics to produce
    detailed reports in both machine-readable (JSON) and human-readable formats.
    
    Example:
        >>> from unischema.validator import UniversalValidator
        >>> from unischema.schema import UserSchema
        >>> from unischema.analysis import ValidationSummary
        >>> 
        >>> validator = UniversalValidator(UserSchema)
        >>> result = validator.validate(df)
        >>> 
        >>> summary = ValidationSummary(result, df)
        >>> report = summary.generate_report()
        >>> summary.save_report("outputs/reports/validation_report.json")
    """
    
    def __init__(
        self,
        validation_result: ValidationResult,
        original_df: pd.DataFrame,
        source_file: Optional[str] = None
    ):
        """
        Initialize the summary generator.
        
        Args:
            validation_result: Result from UniversalValidator.validate()
            original_df: Original DataFrame that was validated
            source_file: Optional path to the source file
        """
        self.result = validation_result
        self.original_df = original_df
        self.source_file = source_file
        self.metrics = DataQualityMetrics(original_df)
        self.generated_at = datetime.now()
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.
        
        Returns:
            Dictionary containing all validation and quality metrics.
        """
        # Get error breakdown by column
        error_counts = self.result.get_error_counts_by_column()
        
        # Get most common errors
        error_summary = self.result.get_error_summary()
        
        return {
            "metadata": {
                "generated_at": self.generated_at.isoformat(),
                "source_file": self.source_file,
                "schema_name": self.result.schema_name,
            },
            "validation_summary": {
                "total_rows": self.result.total_rows,
                "valid_rows": self.result.valid_count,
                "invalid_rows": self.result.invalid_count,
                "success_rate_percent": round(self.result.success_rate, 2),
                "error_rate_percent": round(self.result.error_rate, 2),
                "validation_time_seconds": round(self.result.validation_time, 4),
            },
            "error_analysis": {
                "total_errors": len(self.result.errors),
                "errors_by_column": error_counts,
                "top_error_types": error_summary["most_common_error_types"],
                "sample_errors": [
                    e.to_dict() for e in self.result.errors[:20]
                ],
            },
            "data_quality": self.metrics.compute_all(),
            "quality_issues": self.metrics.get_data_quality_issues(),
        }
    
    def get_terminal_summary(self) -> str:
        """
        Generate a human-readable terminal summary.
        
        Returns:
            Formatted string for terminal output.
        """
        lines = [
            "",
            "=" * 60,
            "  VALIDATION SUMMARY REPORT",
            "=" * 60,
            "",
            f"  Schema:    {self.result.schema_name}",
            f"  Source:    {self.source_file or 'N/A'}",
            f"  Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 60,
            "  VALIDATION RESULTS",
            "-" * 60,
            "",
            f"  Total Rows:   {self.result.total_rows:,}",
            f"  Valid Rows:   {self.result.valid_count:,} ({self.result.success_rate:.1f}%)",
            f"  Invalid Rows: {self.result.invalid_count:,} ({self.result.error_rate:.1f}%)",
            "",
        ]
        
        # Add error breakdown if there are errors
        if self.result.errors:
            error_counts = self.result.get_error_counts_by_column()
            lines.extend([
                "-" * 60,
                "  ERRORS BY COLUMN",
                "-" * 60,
                "",
            ])
            
            sorted_errors = sorted(
                error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for col, count in sorted_errors[:10]:
                bar = "█" * min(count, 30)
                lines.append(f"  {col:<20} {count:>5} {bar}")
            
            lines.append("")
        
        # Add data quality summary
        completeness = self.metrics.compute_completeness_score()
        dup_stats = self.metrics.get_duplicate_stats()
        
        lines.extend([
            "-" * 60,
            "  DATA QUALITY METRICS",
            "-" * 60,
            "",
            f"  Completeness Score: {completeness:.1f}%",
            f"  Duplicate Rows:     {dup_stats['duplicate_rows']:,} ({dup_stats['duplicate_percentage']:.1f}%)",
            "",
        ])
        
        # Add quality issues
        issues = self.metrics.get_data_quality_issues()
        if issues:
            lines.extend([
                "-" * 60,
                "  QUALITY ISSUES DETECTED",
                "-" * 60,
                "",
            ])
            
            for issue in issues[:5]:
                severity_icon = {
                    "high": "[HIGH]",
                    "medium": "[WARNING]",
                    "low": "[INFO]"
                }.get(issue["severity"], "[INFO]")
                
                lines.append(f"  {severity_icon} {issue['description']}")
            
            lines.append("")
        
        lines.extend([
            "=" * 60,
            "",
        ])
        
        return "\n".join(lines)
    
    def save_report(self, output_path: str) -> None:
        """
        Save the validation report to a JSON file.
        
        Args:
            output_path: Path where to save the JSON report.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        report = self.generate_report()
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
    
    def save_valid_data(self, output_path: str) -> None:
        """
        Save valid rows to a CSV file.
        
        Args:
            output_path: Path where to save the CSV.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.result.valid_df.to_csv(output_file, index=False)
    
    def save_invalid_data(self, output_path: str) -> None:
        """
        Save invalid rows to a CSV file.
        
        Args:
            output_path: Path where to save the CSV.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.result.invalid_df.to_csv(output_file, index=False)
    
    def save_all(self, output_dir: str) -> Dict[str, str]:
        """
        Save all outputs: report, valid data, and invalid data.
        
        Args:
            output_dir: Directory to save all outputs.
        
        Returns:
            Dictionary with paths to saved files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = self.generated_at.strftime("%Y%m%d_%H%M%S")
        
        paths = {
            "report": str(output_path / f"validation_report_{timestamp}.json"),
            "valid_data": str(output_path / f"valid_data_{timestamp}.csv"),
            "invalid_data": str(output_path / f"invalid_data_{timestamp}.csv"),
        }
        
        self.save_report(paths["report"])
        
        if not self.result.valid_df.empty:
            self.save_valid_data(paths["valid_data"])
        
        if not self.result.invalid_df.empty:
            self.save_invalid_data(paths["invalid_data"])
        
        return paths
