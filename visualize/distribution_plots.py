"""
Distribution Plots Module

Visualizations for data distributions using matplotlib.
"""

from pathlib import Path
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class DistributionPlots:
    """
    Generate distribution visualizations for DataFrame columns.
    
    Creates histograms, box plots, and other distribution visualizations
    for numeric columns in the dataset.
    
    Example:
        >>> from unischema.visualize import DistributionPlots
        >>> 
        >>> plots = DistributionPlots(df)
        >>> plots.save_histogram("age", "outputs/plots/age_histogram.png")
        >>> plots.save_all_histograms("outputs/plots/")
    """
    
    COLORS = [
        "#3498db", "#2ecc71", "#e74c3c", "#f39c12",
        "#9b59b6", "#1abc9c", "#e67e22", "#34495e"
    ]
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with a DataFrame.
        
        Args:
            df: pandas DataFrame to analyze.
        """
        self.df = df
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Configure matplotlib style."""
        plt.rcParams.update({
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "font.family": "sans-serif",
            "font.size": 10,
        })
    
    def _get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns in the DataFrame."""
        return list(self.df.select_dtypes(include=[np.number]).columns)
    
    def plot_histogram(
        self,
        column: str,
        bins: Union[int, str] = "auto",
        figsize: tuple = (10, 6),
        color: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a histogram for a numeric column.
        
        Args:
            column: Column name to plot.
            bins: Number of bins or 'auto' for automatic.
            figsize: Figure size.
            color: Bar color. Uses default if None.
        
        Returns:
            matplotlib Figure object.
        """
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        data = self.df[column].dropna()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if len(data) == 0:
            ax.text(0.5, 0.5, f"No data in column '{column}'", ha="center", va="center")
            ax.axis("off")
            return fig
        
        # Choose color
        color = color or self.COLORS[0]
        
        # Create histogram
        n, bins_arr, patches = ax.hist(
            data,
            bins=bins,
            color=color,
            edgecolor="white",
            alpha=0.8,
            linewidth=1
        )
        
        # Add statistics
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)
        
        # Add vertical lines for mean and median
        ax.axvline(mean_val, color="#e74c3c", linestyle="--", linewidth=2, label=f"Mean: {mean_val:.2f}")
        ax.axvline(median_val, color="#2ecc71", linestyle="-.", linewidth=2, label=f"Median: {median_val:.2f}")
        
        # Configure axes
        ax.set_xlabel(column, fontweight="bold")
        ax.set_ylabel("Frequency", fontweight="bold")
        ax.set_title(
            f"Distribution of '{column}'\n"
            f"(n={len(data):,}, std={std_val:.2f})",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        
        ax.legend(loc="upper right")
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig
    
    def plot_all_histograms(
        self,
        columns: Optional[List[str]] = None,
        cols_per_row: int = 3,
        figsize_per_plot: tuple = (4, 3)
    ) -> plt.Figure:
        """
        Create a grid of histograms for multiple numeric columns.
        
        Args:
            columns: List of columns to plot. Uses all numeric if None.
            cols_per_row: Number of columns per row in the grid.
            figsize_per_plot: Size of each individual plot.
        
        Returns:
            matplotlib Figure object.
        """
        if columns is None:
            columns = self._get_numeric_columns()
        
        if not columns:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, "No numeric columns to display", ha="center", va="center")
            ax.axis("off")
            return fig
        
        # Calculate grid dimensions
        n_cols = min(cols_per_row, len(columns))
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        # Calculate figure size
        fig_width = figsize_per_plot[0] * n_cols
        fig_height = figsize_per_plot[1] * n_rows
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(fig_width, fig_height))
        
        # Flatten axes for easy iteration
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        # Plot each column
        for idx, column in enumerate(columns):
            ax = axes[idx]
            data = self.df[column].dropna()
            
            if len(data) > 0:
                color = self.COLORS[idx % len(self.COLORS)]
                ax.hist(data, bins="auto", color=color, edgecolor="white", alpha=0.8)
                
                # Add mean line
                ax.axvline(
                    np.mean(data),
                    color="#e74c3c",
                    linestyle="--",
                    linewidth=1.5,
                    alpha=0.8
                )
            
            ax.set_title(column, fontsize=10, fontweight="bold")
            ax.tick_params(axis="both", which="major", labelsize=8)
            ax.yaxis.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(len(columns), len(axes)):
            axes[idx].set_visible(False)
        
        fig.suptitle(
            "Numeric Column Distributions",
            fontsize=14,
            fontweight="bold",
            y=1.02
        )
        
        plt.tight_layout()
        return fig
    
    def plot_boxplot(
        self,
        columns: Optional[List[str]] = None,
        figsize: tuple = (12, 6)
    ) -> plt.Figure:
        """
        Create box plots for numeric columns.
        
        Args:
            columns: List of columns to plot. Uses all numeric if None.
            figsize: Figure size.
        
        Returns:
            matplotlib Figure object.
        """
        if columns is None:
            columns = self._get_numeric_columns()
        
        if not columns:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, "No numeric columns to display", ha="center", va="center")
            ax.axis("off")
            return fig
        
        # Prepare data
        data_to_plot = [self.df[col].dropna().values for col in columns]
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create box plot
        # Matplotlib 3.11 removed 'labels' parameter in favor of 'tick_labels'
        import inspect
        boxplot_kwargs = {"patch_artist": True}
        sig = inspect.signature(ax.boxplot)
        if "tick_labels" in sig.parameters:
            boxplot_kwargs["tick_labels"] = columns
        else:
            boxplot_kwargs["labels"] = columns
            
        bp = ax.boxplot(
            data_to_plot,
            **boxplot_kwargs
        )
        
        # Color boxes
        for idx, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(self.COLORS[idx % len(self.COLORS)])
            patch.set_alpha(0.7)
        
        # Style whiskers and caps
        for whisker in bp["whiskers"]:
            whisker.set_color("#34495e")
            whisker.set_linewidth(1.5)
        
        for cap in bp["caps"]:
            cap.set_color("#34495e")
            cap.set_linewidth(1.5)
        
        for median in bp["medians"]:
            median.set_color("#e74c3c")
            median.set_linewidth(2)
        
        ax.set_xticklabels(columns, rotation=45, ha="right")
        ax.set_ylabel("Value", fontweight="bold")
        ax.set_title(
            "Box Plot Comparison of Numeric Columns",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig
    
    def plot_correlation_matrix(self, figsize: tuple = (10, 8)) -> plt.Figure:
        """
        Create a correlation matrix heatmap for numeric columns.
        
        Args:
            figsize: Figure size.
        
        Returns:
            matplotlib Figure object.
        """
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if numeric_df.empty or len(numeric_df.columns) < 2:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(
                0.5, 0.5,
                "Need at least 2 numeric columns for correlation",
                ha="center", va="center"
            )
            ax.axis("off")
            return fig
        
        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create heatmap
        im = ax.imshow(corr_matrix.values, cmap="RdBu_r", aspect="auto", vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Correlation", fontweight="bold")
        
        # Configure ticks
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.columns)))
        ax.set_xticklabels(corr_matrix.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr_matrix.columns)
        
        # Add correlation values as text
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                value = corr_matrix.iloc[i, j]
                text_color = "white" if abs(value) > 0.5 else "black"
                ax.text(
                    j, i, f"{value:.2f}",
                    ha="center", va="center",
                    color=text_color, fontsize=9
                )
        
        ax.set_title(
            "Correlation Matrix",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        
        plt.tight_layout()
        return fig
    
    def save_histogram(self, column: str, path: str, **kwargs) -> None:
        """Save single histogram to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_histogram(column, **kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_all_histograms(self, output_dir: str, **kwargs) -> str:
        """Save grid of all histograms to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        path = str(output_path / "numeric_distributions.png")
        fig = self.plot_all_histograms(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        
        return path
    
    def save_boxplot(self, path: str, **kwargs) -> None:
        """Save box plot to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_boxplot(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_correlation_matrix(self, path: str, **kwargs) -> None:
        """Save correlation matrix to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_correlation_matrix(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_all(self, output_dir: str) -> List[str]:
        """
        Save all distribution plots to a directory.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        numeric_cols = self._get_numeric_columns()
        
        if numeric_cols:
            # Save combined histograms
            path = self.save_all_histograms(str(output_path))
            saved_files.append(path)
            
            # Save box plot
            path = str(output_path / "boxplot.png")
            self.save_boxplot(path)
            saved_files.append(path)
            
            # Save correlation matrix if enough columns
            if len(numeric_cols) >= 2:
                path = str(output_path / "correlation_matrix.png")
                self.save_correlation_matrix(path)
                saved_files.append(path)
        
        return saved_files
