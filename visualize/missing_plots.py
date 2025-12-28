"""
Missing Values Plots Module

Visualizations for missing data analysis using matplotlib.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

from ..analysis.metrics import DataQualityMetrics


class MissingPlots:
    """
    Generate visualizations for missing data analysis.
    
    Creates heatmaps, bar charts, and pattern visualizations for
    understanding missing data in the dataset.
    
    Example:
        >>> from unischema.visualize import MissingPlots
        >>> 
        >>> plots = MissingPlots(df)
        >>> plots.save_missing_heatmap("outputs/plots/missing_heatmap.png")
        >>> plots.save_missing_bar("outputs/plots/missing_bar.png")
    """
    
    COLORS = {
        "missing": "#e74c3c",
        "present": "#2ecc71",
        "neutral": "#95a5a6",
    }
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with a DataFrame.
        
        Args:
            df: pandas DataFrame to analyze.
        """
        self.df = df
        self.metrics = DataQualityMetrics(df)
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Configure matplotlib style."""
        plt.rcParams.update({
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.grid": False,
            "font.family": "sans-serif",
            "font.size": 10,
        })
    
    def plot_missing_heatmap(
        self,
        figsize: Optional[tuple] = None,
        max_rows: int = 100,
        max_columns: int = 30
    ) -> plt.Figure:
        """
        Create a heatmap-style plot showing missing value locations.
        
        White cells indicate present values, colored cells indicate missing.
        
        Args:
            figsize: Figure size. Auto-calculated if None.
            max_rows: Maximum rows to display.
            max_columns: Maximum columns to display.
        
        Returns:
            matplotlib Figure object.
        """
        # Prepare data
        df_display = self.df.iloc[:max_rows, :max_columns]
        
        # Create binary missing matrix (1 = missing, 0 = present)
        missing_matrix = df_display.isnull().astype(int).values
        
        # Calculate figure size
        if figsize is None:
            width = max(8, min(len(df_display.columns) * 0.5, 20))
            height = max(6, min(len(df_display) * 0.1, 15))
            figsize = (width, height)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create custom colormap (white for present, red for missing)
        cmap = mcolors.ListedColormap(["#f0f0f0", "#e74c3c"])
        
        # Create heatmap
        im = ax.imshow(missing_matrix, aspect="auto", cmap=cmap, interpolation="nearest")
        
        # Configure axes
        ax.set_xticks(range(len(df_display.columns)))
        ax.set_xticklabels(df_display.columns, rotation=45, ha="right", fontsize=8)
        
        # Limit y-axis ticks for readability
        if len(df_display) > 20:
            ytick_step = len(df_display) // 10
            ax.set_yticks(range(0, len(df_display), ytick_step))
        
        ax.set_xlabel("Columns", fontweight="bold")
        ax.set_ylabel("Row Index", fontweight="bold")
        
        # Calculate missing stats
        total_missing = int(missing_matrix.sum())
        total_cells = missing_matrix.size
        missing_pct = (total_missing / total_cells) * 100 if total_cells > 0 else 0
        
        ax.set_title(
            f"Missing Values Heatmap\n"
            f"(Missing: {total_missing:,} cells, {missing_pct:.1f}%)",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#f0f0f0", edgecolor="gray", label="Present"),
            Patch(facecolor="#e74c3c", edgecolor="gray", label="Missing"),
        ]
        ax.legend(handles=legend_elements, loc="upper right", framealpha=0.9)
        
        plt.tight_layout()
        return fig
    
    def plot_missing_bar(
        self,
        figsize: tuple = (12, 6),
        show_percentages: bool = True
    ) -> plt.Figure:
        """
        Create a bar chart showing missing value percentage per column.
        
        Args:
            figsize: Figure size.
            show_percentages: Whether to show percentage labels.
        
        Returns:
            matplotlib Figure object.
        """
        missing_info = self.metrics.get_missing_values()
        missing_by_col = missing_info["missing_by_column"]
        
        # Sort by missing percentage
        sorted_cols = sorted(
            missing_by_col.items(),
            key=lambda x: x[1]["percentage"],
            reverse=True
        )
        
        columns = [item[0] for item in sorted_cols]
        percentages = [item[1]["percentage"] for item in sorted_cols]
        counts = [item[1]["count"] for item in sorted_cols]
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create gradient colors based on percentage
        colors = []
        for pct in percentages:
            if pct > 50:
                colors.append("#e74c3c")  # Red for high missing
            elif pct > 20:
                colors.append("#f39c12")  # Orange for moderate
            elif pct > 0:
                colors.append("#f1c40f")  # Yellow for low
            else:
                colors.append("#2ecc71")  # Green for complete
        
        bars = ax.bar(range(len(columns)), percentages, color=colors, edgecolor="white")
        
        # Add percentage labels
        if show_percentages:
            for bar, pct, count in zip(bars, percentages, counts):
                height = bar.get_height()
                if height > 0:
                    label = f"{pct:.1f}%\n({count:,})"
                    ax.annotate(
                        label,
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8
                    )
        
        # Configure axes
        ax.set_xticks(range(len(columns)))
        ax.set_xticklabels(columns, rotation=45, ha="right")
        ax.set_xlabel("Column", fontweight="bold")
        ax.set_ylabel("Missing Percentage (%)", fontweight="bold")
        ax.set_ylim(0, max(percentages) * 1.2 if percentages else 100)
        
        ax.set_title(
            f"Missing Values by Column\n"
            f"(Overall: {missing_info['overall_missing_percentage']:.1f}% missing)",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        
        # Add horizontal line at thresholds
        ax.axhline(y=20, color="#f39c12", linestyle="--", alpha=0.5, label="20% threshold")
        ax.axhline(y=50, color="#e74c3c", linestyle="--", alpha=0.5, label="50% threshold")
        ax.legend(loc="upper right")
        
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        return fig
    
    def plot_missing_pattern(
        self,
        figsize: tuple = (10, 8),
        max_patterns: int = 20
    ) -> plt.Figure:
        """
        Visualize patterns of missing data across columns.
        
        Shows which columns tend to be missing together.
        
        Args:
            figsize: Figure size.
            max_patterns: Maximum number of patterns to show.
        
        Returns:
            matplotlib Figure object.
        """
        # Create missing indicator matrix
        missing = self.df.isnull()
        
        # Get unique patterns
        patterns = missing.drop_duplicates()
        pattern_counts = missing.value_counts().head(max_patterns)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if len(pattern_counts) == 0:
            ax.text(0.5, 0.5, "No missing data patterns found", ha="center", va="center")
            ax.axis("off")
            return fig
        
        # Prepare pattern matrix for visualization
        pattern_matrix = []
        pattern_labels = []
        
        for pattern, count in pattern_counts.items():
            if isinstance(pattern, tuple):
                pattern_matrix.append(list(pattern))
                pattern_labels.append(f"n={count:,}")
            else:
                pattern_matrix.append([pattern])
                pattern_labels.append(f"n={count:,}")
        
        pattern_array = np.array(pattern_matrix, dtype=int)
        
        # Create heatmap
        cmap = mcolors.ListedColormap(["#f0f0f0", "#e74c3c"])
        im = ax.imshow(pattern_array, aspect="auto", cmap=cmap, interpolation="nearest")
        
        # Configure axes
        ax.set_xticks(range(len(self.df.columns)))
        ax.set_xticklabels(self.df.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(pattern_labels)))
        ax.set_yticklabels(pattern_labels, fontsize=9)
        
        ax.set_xlabel("Columns", fontweight="bold")
        ax.set_ylabel("Pattern (count)", fontweight="bold")
        ax.set_title(
            "Missing Data Patterns\n(Top patterns by frequency)",
            fontsize=12,
            fontweight="bold",
            pad=15
        )
        
        plt.tight_layout()
        return fig
    
    def save_missing_heatmap(self, path: str, **kwargs) -> None:
        """Save missing values heatmap to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_missing_heatmap(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_missing_bar(self, path: str, **kwargs) -> None:
        """Save missing values bar chart to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_missing_bar(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_missing_pattern(self, path: str, **kwargs) -> None:
        """Save missing patterns visualization to file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fig = self.plot_missing_pattern(**kwargs)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    
    def save_all(self, output_dir: str) -> List[str]:
        """
        Save all missing data plots to a directory.
        
        Args:
            output_dir: Directory to save plots.
        
        Returns:
            List of saved file paths.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save heatmap
        path = str(output_path / "missing_heatmap.png")
        self.save_missing_heatmap(path)
        saved_files.append(path)
        
        # Save bar chart
        path = str(output_path / "missing_bar.png")
        self.save_missing_bar(path)
        saved_files.append(path)
        
        # Save pattern if there's missing data
        if self.df.isnull().any().any():
            path = str(output_path / "missing_pattern.png")
            self.save_missing_pattern(path)
            saved_files.append(path)
        
        return saved_files
