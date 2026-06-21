import pytest
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Set non-interactive backend for unit testing
from pathlib import Path
from unischema.visualize import ErrorPlots, MissingPlots, DistributionPlots, ReportGenerator
from unischema.validator import ValidationResult, ValidationError


@pytest.fixture
def sample_visual_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": ["Alice", "Bob", None, "Dave"],
        "age": [25, 30, 35, 40],
        "salary": [50000.0, 60000.0, 70000.0, None]
    })


@pytest.fixture
def mock_visual_result():
    errors = [
        ValidationError(row_index=2, column="name", error_type="missing", message="Missing", value=None),
        ValidationError(row_index=3, column="salary", error_type="type_error", message="Missing", value=None),
    ]
    valid_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"], "age": [25, 30], "salary": [50000.0, 60000.0]})
    invalid_df = pd.DataFrame({"id": [3, 4], "name": [None, "Dave"], "age": [35, 40], "salary": [70000.0, None]})
    return ValidationResult(
        valid_df=valid_df,
        invalid_df=invalid_df,
        errors=errors,
        total_rows=4,
        valid_count=2,
        invalid_count=2,
        validation_time=0.1,
        schema_name="MockSchema"
    )


def test_error_plots(mock_visual_result, tmp_path):
    plots = ErrorPlots(mock_visual_result)
    
    # Verify figures are created successfully
    fig1 = plots.plot_errors_by_column()
    assert fig1 is not None
    matplotlib.pyplot.close(fig1)
    
    fig2 = plots.plot_valid_invalid_pie()
    assert fig2 is not None
    matplotlib.pyplot.close(fig2)
    
    fig3 = plots.plot_error_types()
    assert fig3 is not None
    matplotlib.pyplot.close(fig3)
    
    # Verify saving works
    out_dir = tmp_path / "errors"
    saved = plots.save_all(str(out_dir))
    assert len(saved) == 3
    assert all(Path(p).exists() for p in saved)


def test_missing_plots(sample_visual_df, tmp_path):
    plots = MissingPlots(sample_visual_df)
    
    fig1 = plots.plot_missing_heatmap()
    assert fig1 is not None
    matplotlib.pyplot.close(fig1)
    
    fig2 = plots.plot_missing_bar()
    assert fig2 is not None
    matplotlib.pyplot.close(fig2)
    
    fig3 = plots.plot_missing_pattern()
    assert fig3 is not None
    matplotlib.pyplot.close(fig3)
    
    out_dir = tmp_path / "missing"
    saved = plots.save_all(str(out_dir))
    assert len(saved) == 3
    assert all(Path(p).exists() for p in saved)


def test_distribution_plots(sample_visual_df, tmp_path):
    plots = DistributionPlots(sample_visual_df)
    
    fig1 = plots.plot_histogram("age")
    assert fig1 is not None
    matplotlib.pyplot.close(fig1)
    
    fig2 = plots.plot_all_histograms()
    assert fig2 is not None
    matplotlib.pyplot.close(fig2)
    
    fig3 = plots.plot_boxplot()
    assert fig3 is not None
    matplotlib.pyplot.close(fig3)
    
    fig4 = plots.plot_correlation_matrix()
    assert fig4 is not None
    matplotlib.pyplot.close(fig4)
    
    out_dir = tmp_path / "dist"
    saved = plots.save_all(str(out_dir))
    assert len(saved) == 3  # histograms, boxplot, correlation
    assert all(Path(p).exists() for p in saved)


def test_report_generator(mock_visual_result, sample_visual_df, tmp_path):
    generator = ReportGenerator(
        validation_result=mock_visual_result,
        original_df=sample_visual_df,
        source_file="mock_data.csv"
    )
    
    out_dir = tmp_path / "report_out"
    outputs = generator.generate_all(str(out_dir))
    
    assert "error_plots" in outputs
    assert "missing_plots" in outputs
    assert "distribution_plots" in outputs
    assert "reports" in outputs
    
    # Check that outputs actually exist on filesystem
    assert len(outputs["error_plots"]) == 3
    assert len(outputs["missing_plots"]) == 3
    assert len(outputs["distribution_plots"]) == 3
    assert len(outputs["reports"]) == 3
    
    summary_text = generator.get_output_summary(outputs)
    assert "Total files generated" in summary_text
