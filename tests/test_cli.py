import pytest
import pandas as pd
from pathlib import Path
from unischema.cli import main


@pytest.fixture
def cli_csv_file(tmp_path):
    csv_file = tmp_path / "cli_users.csv"
    df = pd.DataFrame({
        "id": [1, 2],
        "name": ["Alice", "Bob"],
        "email": ["alice@example.com", "bob@example.com"],
        "age": [25, 30],
        "phone": ["123-456-7890", "098-765-4321"],
        "is_active": [True, False]
    })
    df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def cli_invalid_csv_file(tmp_path):
    csv_file = tmp_path / "cli_invalid.csv"
    # id is negative (fails UserSchema gt=0), age is too high (fails le=120)
    df = pd.DataFrame({
        "id": [-1, 2],
        "name": ["Alice", "Bob"],
        "email": ["alice@example.com", "bob@example.com"],
        "age": [150, 30],
        "phone": ["123-456-7890", "098-765-4321"],
        "is_active": [True, False]
    })
    df.to_csv(csv_file, index=False)
    return csv_file


def test_cli_schemas_command(capsys):
    exit_code = main(["schemas"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Available Schemas" in captured.out
    assert "UserSchema" in captured.out
    assert "EmployeeSchema" in captured.out


def test_cli_info_command(cli_csv_file, capsys):
    exit_code = main(["info", "--file", str(cli_csv_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "File Information" in captured.out
    assert "cli_users.csv" in captured.out
    assert "CSVLoader" in captured.out
    assert "Rows: 2" in captured.out


def test_cli_info_file_not_found(capsys):
    exit_code = main(["info", "--file", "nonexistent.csv"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error: File not found" in captured.out


def test_cli_check_success(cli_csv_file, capsys):
    exit_code = main(["check", "--file", str(cli_csv_file), "--schema", "user"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "VALIDATION SUMMARY REPORT" in captured.out
    assert "Valid Rows:   2" in captured.out
    assert "Invalid Rows: 0" in captured.out


def test_cli_check_failure(cli_invalid_csv_file, capsys):
    exit_code = main(["check", "--file", str(cli_invalid_csv_file), "--schema", "user"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "VALIDATION SUMMARY REPORT" in captured.out
    assert "Valid Rows:   1" in captured.out
    assert "Invalid Rows: 1" in captured.out
    assert "id" in captured.out or "age" in captured.out


def test_cli_check_with_output(cli_csv_file, tmp_path, capsys):
    out_dir = tmp_path / "cli_outputs"
    exit_code = main(["check", "--file", str(cli_csv_file), "--schema", "user", "--output", str(out_dir)])
    assert exit_code == 0
    
    # Check output folder files
    assert (out_dir / "plots" / "errors_by_column.png").exists()
    assert (out_dir / "plots" / "valid_invalid_pie.png").exists()
    
    # JSON report should exist
    report_files = list((out_dir / "reports").glob("validation_report_*.json"))
    assert len(report_files) == 1
