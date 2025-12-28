"""
Report Generator Module

Orchestrates all visualization outputs into comprehensive reports.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd

from ..validator.validator import ValidationResult
from ..analysis.summary import ValidationSummary
from .error_plots import ErrorPlots
from .missing_plots import MissingPlots
from .distribution_plots import DistributionPlots


class ReportGenerator:
    """
    Generates comprehensive visual reports for validation results.
    
    Orchestrates all visualization modules to produce a complete set
    of plots and export them to a specified directory.
    
    Example:
        >>> from unischema.visualize import ReportGenerator
        >>> 
        >>> generator = ReportGenerator(
        ...     validation_result=result,
        ...     original_df=df,
        ...     source_file="data/users.csv"
        ... )
        >>> 
        >>> saved_files = generator.generate_all("outputs/")
        >>> print(f"Generated {len(saved_files)} files")
    """
    
    def __init__(
        self,
        validation_result: ValidationResult,
        original_df: pd.DataFrame,
        source_file: Optional[str] = None
    ):
        """
        Initialize the report generator.
        
        Args:
            validation_result: Result from UniversalValidator.validate()
            original_df: Original DataFrame that was validated
            source_file: Optional path to the source file
        """
        self.result = validation_result
        self.original_df = original_df
        self.source_file = source_file
        
        # Initialize visualization modules
        self.error_plots = ErrorPlots(validation_result)
        self.missing_plots = MissingPlots(original_df)
        self.distribution_plots = DistributionPlots(original_df)
        self.summary = ValidationSummary(validation_result, original_df, source_file)
    
    def generate_error_plots(self, output_dir: str) -> List[str]:
        """
        Generate all error-related plots.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        plots_dir = Path(output_dir) / "plots"
        return self.error_plots.save_all(str(plots_dir))
    
    def generate_missing_plots(self, output_dir: str) -> List[str]:
        """
        Generate all missing data plots.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        plots_dir = Path(output_dir) / "plots"
        return self.missing_plots.save_all(str(plots_dir))
    
    def generate_distribution_plots(self, output_dir: str) -> List[str]:
        """
        Generate all distribution plots.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        plots_dir = Path(output_dir) / "plots"
        return self.distribution_plots.save_all(str(plots_dir))
    
    def generate_reports(self, output_dir: str) -> Dict[str, str]:
        """
        Generate JSON and CSV reports.
        
        Args:
            output_dir: Directory to save reports.
        
        Returns:
            Dictionary with paths to saved files.
        """
        reports_dir = Path(output_dir) / "reports"
        return self.summary.save_all(str(reports_dir))
    
    def generate_all(self, output_dir: str) -> Dict[str, Any]:
        """
        Generate all plots and reports.
        
        Args:
            output_dir: Base output directory.
        
        Returns:
            Dictionary with all saved file paths organized by type.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        all_outputs: Dict[str, Any] = {
            "error_plots": [],
            "missing_plots": [],
            "distribution_plots": [],
            "reports": {},
        }
        
        # Generate error plots
        all_outputs["error_plots"] = self.generate_error_plots(str(output_path))
        
        # Generate missing plots
        all_outputs["missing_plots"] = self.generate_missing_plots(str(output_path))
        
        # Generate distribution plots
        all_outputs["distribution_plots"] = self.generate_distribution_plots(str(output_path))
        
        # Generate reports
        all_outputs["reports"] = self.generate_reports(str(output_path))
        
        return all_outputs
    
    def get_output_summary(self, outputs: Dict[str, Any]) -> str:
        """
        Get a summary of generated outputs.
        
        Args:
            outputs: Dictionary from generate_all()
        
        Returns:
            Formatted summary string.
        """
        lines = [
            "",
            "=" * 50,
            "  GENERATED OUTPUTS",
            "=" * 50,
            "",
        ]
        
        total_files = 0
        
        for category, files in outputs.items():
            if isinstance(files, list):
                count = len(files)
                total_files += count
                lines.append(f"  {category}: {count} files")
                for f in files:
                    lines.append(f"    - {Path(f).name}")
            elif isinstance(files, dict):
                count = len(files)
                total_files += count
                lines.append(f"  {category}: {count} files")
                for key, f in files.items():
                    lines.append(f"    - {key}: {Path(f).name}")
            lines.append("")
        
        lines.extend([
            "-" * 50,
            f"  Total files generated: {total_files}",
            "=" * 50,
            "",
        ])
        
        return "\n".join(lines)
    
    def print_terminal_summary(self) -> None:
        """Print the validation summary to terminal."""
        print(self.summary.get_terminal_summary())
