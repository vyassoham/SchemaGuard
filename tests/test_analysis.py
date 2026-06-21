import pytest
import pandas as pd
import json
from pathlib import Path
from unischema.analysis import DataQualityMetrics, ValidationSummary
from unischema.analysis.metrics import ColumnMetrics
from unischema.validator import ValidationResult, ValidationError


@pytest.fixture
def sample_metrics_df():
    return pd.DataFrame({
        "id": [1, 2, 2, 4],  # duplicate row index 2, duplicate id
        "name": ["Alice", "Bob", "Bob", None],  # missing name
        "score": [90.5, 80.0, 80.0, 70.0],
        "is_staff": [True, False, False, True]
    })


@pytest.fixture
def mock_validation_result():
    # We mock a validation result with 1 valid row, 1 invalid row, 1 error
    valid_df = pd.DataFrame({"id": [1], "name": ["Alice"]})
    invalid_df = pd.DataFrame({"id": [4], "name": [None]})
    errors = [
        ValidationError(row_index=3, column="name", error_type="missing", message="Field required", value=None)
    ]
    return ValidationResult(
        valid_df=valid_df,
        invalid_df=invalid_df,
        errors=errors,
        total_rows=2,
        valid_count=1,
        invalid_count=1,
        validation_time=0.05,
        schema_name="MockSchema"
    )


def test_column_metrics_to_dict():
    # Test numeric column metrics conversion
    num_metrics = ColumnMetrics(
        column_name="score",
        dtype="float64",
        total_count=10,
        non_null_count=10,
        null_count=0,
        null_percentage=0.0,
        unique_count=5,
        unique_percentage=50.0,
        mean=85.0,
        median=85.0,
        std=5.0,
        min_value=75.0,
        max_value=95.0,
        q25=80.0,
        q75=90.0
    )
    d = num_metrics.to_dict()
    assert d["column_name"] == "score"
    assert d["mean"] == 85.0
    assert "avg_length" not in d

    # Test string column metrics conversion
    str_metrics = ColumnMetrics(
        column_name="name",
        dtype="object",
        total_count=10,
        non_null_count=8,
        null_count=2,
        null_percentage=20.0,
        unique_count=4,
        unique_percentage=50.0,
        avg_length=4.5,
        min_length=3,
        max_length=6
    )
    d_str = str_metrics.to_dict()
    assert d_str["column_name"] == "name"
    assert d_str["avg_length"] == 4.5
    assert "mean" not in d_str


def test_data_quality_metrics(sample_metrics_df):
    metrics = DataQualityMetrics(sample_metrics_df)
    
    assert metrics.total_rows == 4
    assert metrics.total_columns == 4
    
    # Basic Stats
    basic = metrics.get_basic_stats()
    assert basic["total_rows"] == 4
    assert basic["total_columns"] == 4
    assert basic["memory_usage_bytes"] > 0

    # Missing values
    missing = metrics.get_missing_values()
    assert missing["total_missing_values"] == 1
    assert missing["columns_with_missing"] == 1
    assert missing["missing_by_column"]["name"]["count"] == 1

    # Duplicate rows
    dup = metrics.get_duplicate_stats()
    assert dup["duplicate_rows"] == 1
    assert dup["unique_rows"] == 3
    assert dup["duplicate_percentage"] == 25.0

    # Column metrics
    id_metrics = metrics.get_column_metrics("id")
    assert id_metrics.unique_count == 3
    
    score_metrics = metrics.get_column_metrics("score")
    assert score_metrics.mean == 80.125
    assert score_metrics.min_value == 70.0

    name_metrics = metrics.get_column_metrics("name")
    assert name_metrics.null_count == 1
    assert name_metrics.avg_length == pytest.approx(3.67, abs=0.01)

    # Completeness Score
    comp = metrics.compute_completeness_score()
    # Total cells: 16, missing: 1, filled: 15. 15/16 * 100 = 93.75
    assert comp == 93.75

    # Data Quality Issues
    issues = metrics.get_data_quality_issues()
    assert len(issues) > 0  # should highlight duplicate rows or others


def test_validation_summary(mock_validation_result, sample_metrics_df, tmp_path):
    summary = ValidationSummary(
        validation_result=mock_validation_result,
        original_df=sample_metrics_df,
        source_file="test_source.csv"
    )
    
    report = summary.generate_report()
    assert report["metadata"]["source_file"] == "test_source.csv"
    assert report["validation_summary"]["valid_rows"] == 1
    assert len(report["error_analysis"]["sample_errors"]) == 1
    
    # Terminal summary
    term = summary.get_terminal_summary()
    assert "VALIDATION SUMMARY REPORT" in term
    assert "MockSchema" in term
    assert "test_source.csv" in term
    
    # File saving
    report_file = tmp_path / "report.json"
    valid_file = tmp_path / "valid.csv"
    invalid_file = tmp_path / "invalid.csv"
    
    summary.save_report(str(report_file))
    summary.save_valid_data(str(valid_file))
    summary.save_invalid_data(str(invalid_file))
    
    assert report_file.exists()
    assert valid_file.exists()
    assert invalid_file.exists()
    
    # Test save_all
    out_dir = tmp_path / "outputs"
    paths = summary.save_all(str(out_dir))
    assert Path(paths["report"]).exists()
    assert Path(paths["valid_data"]).exists()
    assert Path(paths["invalid_data"]).exists()
