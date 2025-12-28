"""
Error Plots Module

Visualizations for validation errors using matplotlib.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from ..validator.validator import ValidationResult


class ErrorPlots:
    """
    Generate error-related visualizations for validation results.
    
    Creates bar charts, pie charts, and other visualizations to help
    understand validation error patterns.
    
    Example:
        >>> from unischema.visualize import ErrorPlots
        >>> 
        >>> plots = ErrorPlots(validation_result)
        >>> plots.save_errors_by_column("outputs/plots/errors_by_column.png")
        >>> plots.save_valid_invalid_pie("outputs/plots/valid_invalid.png")
    """
    
    # Color palette for consistent styling
    COLORS = {
        "primary": "#3498db",
        "danger": "#e74c3c",
        "success": "#2ecc71",
        "warning": "#f39c12",
        "secondary": "#95a5a6",
    }
    
    # Gradient colors for bar charts
    BAR_COLORS = [
        "#e74c3c", "#c0392b", "#9b59b6", "#8e44ad",
        "#3498db", "#2980b9", "#1abc9c", "#16a085",
        "#f39c12", "#e67e22"
    ]
    
    def __init__(self, result: ValidationResult):
        """
        Initialize with validation result.
        
        Args:
            result: ValidationResult from UniversalValidator.
        """
        self.result = result
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Configure matplotlib style for clean, professional plots."""
        plt.rcParams.update({
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "--",
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
        })
    
    def plot_errors_by_column(
        self,
        figsize: tuple = (12, 6),
        max_columns: int = 15
    ) -> plt.Figure:
        """
        Create a bar chart showing error counts per column.
        
        Args:
            figsize: Figure size as (width, height).
            max_columns: Maximum number of columns to display.
        
        Returns:
            matplotlib Figure object.
        """
        error_counts = self.result.get_error_counts_by_column()
        
        if not error_counts:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5, 0.5,
                "No validation errors found!",
                ha="center", va="center",
                fontsize=14,
                color=self.COLORS["success"]
            )
            ax.axis("off")
            plt.title("Validation Errors by Column", fontsize=14, fontweight="bold")
            return fig
        
        # Sort and limit columns
        sorted_errors = sorted(
            error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_columns]
        
        columns = [item[0] for item in sorted_errors]
        counts = [item[1] for item in sorted_errors]
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create bars with gradient colors
        colors = [self.BAR_COLORS[i % len(self.BAR_COLORS)] for i in range(len(columns))]
        bars = ax.bar(range(len(columns)), counts, color=colors, edgecolor="white", linewidth=0.5)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.annotate(
                f"{count:,}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )
        
        # Configure axes
        ax.set_xticks(range(len(columns)))
        ax.set_xticklabels(columns, rotation=45, ha="right")
        ax.set_xlabel("Column", fontweight="bold")
        ax.set_ylabel("Error Count", fontweight="bold")
        ax.set_title(
            f"Validation Errors by Column (Total: {len(self.result.errors):,} errors)",
            fontsize=14,
            fontweight="bold",
            pad=15
        )
        
        # Add grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig
    
    def plot_valid_invalid_pie(self, figsize: tuple = (8, 8)) -> plt.Figure:
        """
        Create a pie chart showing valid vs invalid row distribution.
        
        Args:
            figsize: Figure size as (width, height).
        
        Returns:
            matplotlib Figure object.
        """
        valid = self.result.valid_count
        invalid = self.result.invalid_count
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Data
        sizes = [valid, invalid]
        labels = [
            f"Valid\n({valid:,} rows)",
            f"Invalid\n({invalid:,} rows)"
        ]
        colors = [self.COLORS["success"], self.COLORS["danger"]]
        explode = (0.02, 0.05)  # Slightly explode invalid slice
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct=lambda pct: f"{pct:.1f}%",
            startangle=90,
            shadow=False,
            wedgeprops={"edgecolor": "white", "linewidth": 2}
        )
        
        # Style the percentage text
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(12)
            autotext.set_fontweight("bold")
        
        # Style labels
        for text in texts:
            text.set_fontsize(11)
        
        ax.set_title(
            f"Validation Results\n(Total: {self.result.total_rows:,} rows)",
            fontsize=14,
            fontweight="bold",
            pad=20
        )
        
        plt.tight_layout()
        return fig
    
    def plot_error_types(self, figsize: tuple = (10, 6)) -> plt.Figure:
        """
        Create a horizontal bar chart of error types.
        
        Args:
            figsize: Figure size as (width, height).
        
        Returns:
            matplotlib Figure object.
        """
        error_types: Dict[str, int] = {}
        for error in self.result.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        
        if not error_types:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No errors to display", ha="center", va="center")
            ax.axis("off")
            return fig
        
        sorted_types = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
        types = [item[0] for item in sorted_types]
        counts = [item[1] for item in sorted_types]
        
        fig, ax = plt.subplots(figsize=figsize)
        
        y_pos = np.arange(len(types))
        colors = [self.BAR_COLORS[i % len(self.BAR_COLORS)] for i in range(len(types))]
        
        bars = ax.barh(y_pos, counts, color=colors, edgecolor="white", height=0.6)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.annotate(
                f"{count:,}",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold"
            )
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(types)
        ax.set_xlabel("Error Count", fontweight="bold")
        ax.set_title("Error Types Distribution", fontsize=14, fontweight="bold", pad=15)
        ax.invert_yaxis()
        ax.xaxis.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def save_errors_by_column(self, path: str, **kwargs) -> None:
        """Save errors by column bar chart to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_errors_by_column(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_valid_invalid_pie(self, path: str, **kwargs) -> None:
        """Save valid/invalid pie chart to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_valid_invalid_pie(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_error_types(self, path: str, **kwargs) -> None:
        """Save error types chart to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_error_types(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_all(self, output_dir: str) -> List[str]:
        """
        Save all error plots to a directory.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save errors by column
        path = str(output_path / "errors_by_column.png")
        self.save_errors_by_column(path)
        saved_files.append(path)
        
        # Save pie chart
        path = str(output_path / "valid_invalid_pie.png")
        self.save_valid_invalid_pie(path)
        saved_files.append(path)
        
        # Save error types
        if self.result.errors:
            path = str(output_path / "error_types.png")
            self.save_error_types(path)
            saved_files.append(path)
        
        return saved_files
