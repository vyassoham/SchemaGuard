import pytest
import pandas as pd
import json
from pathlib import Path
from unischema.loaders import LoaderFactory, CSVLoader, ExcelLoader, JSONLoader, PDFLoader


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
        "age": [25, 30, 35],
        "phone": ["1234567890", "0987654321", None],
        "is_active": [True, False, True]
    })


def test_csv_loader(tmp_path, sample_data):
    csv_file = tmp_path / "users.csv"
    sample_data.to_csv(csv_file, index=False)
    
    loader = CSVLoader(str(csv_file))
    df = loader.load()
    
    assert len(df) == 3
    assert list(df.columns) == ["id", "name", "email", "age", "phone", "is_active"]
    assert df.loc[0, "name"] == "Alice"


def test_tsv_loader(tmp_path, sample_data):
    tsv_file = tmp_path / "users.tsv"
    sample_data.to_csv(tsv_file, sep="\t", index=False)
    
    loader = CSVLoader(str(tsv_file))
    df = loader.load()
    
    assert len(df) == 3
    assert df.loc[1, "name"] == "Bob"


def test_excel_loader(tmp_path, sample_data):
    excel_file = tmp_path / "users.xlsx"
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        sample_data.to_excel(writer, sheet_name="ActiveUsers", index=False)
    
    loader = ExcelLoader(str(excel_file))
    sheets = loader.get_sheet_names()
    assert "ActiveUsers" in sheets
    
    df = loader.load()
    assert len(df) == 3
    assert df.loc[0, "name"] == "Alice"


def test_json_loader(tmp_path, sample_data):
    # Standard JSON array of objects
    json_file = tmp_path / "users.json"
    records = sample_data.to_dict(orient="records")
    with open(json_file, "w") as f:
        json.dump(records, f)
        
    loader = JSONLoader(str(json_file))
    df = loader.load()
    assert len(df) == 3
    assert df.loc[0, "name"] == "Alice"


def test_jsonl_loader(tmp_path, sample_data):
    jsonl_file = tmp_path / "users.jsonl"
    sample_data.to_json(jsonl_file, orient="records", lines=True)
    
    loader = JSONLoader(str(jsonl_file))
    df = loader.load()
    assert len(df) == 3
    assert df.loc[2, "name"] == "Charlie"


def test_pdf_loader(tmp_path):
    try:
        import tabula
    except ImportError:
        pytest.skip("tabula-py is not installed. PDF loading is an optional dependency.")
    pdf_file = tmp_path / "users.pdf"
    # Create an empty file to satisfy path existence checks
    pdf_file.write_bytes(b"dummy pdf content")
    
    loader = PDFLoader(str(pdf_file))
    assert loader.get_table_count() == 1
    
    df = loader.load()
    assert len(df) == 2
    assert df.loc[0, "name"] == "Alice"
    assert loader.combine_all_tables().shape == (2, 7)  # 6 cols + _table_index


def test_loader_factory(tmp_path, sample_data):
    csv_file = tmp_path / "test.csv"
    sample_data.to_csv(csv_file, index=False)
    
    assert LoaderFactory.is_supported(str(csv_file))
    assert not LoaderFactory.is_supported("test.invalid")
    
    df = LoaderFactory.load(str(csv_file))
    assert len(df) == 3
    
    info = LoaderFactory.get_loader_info(str(csv_file))
    assert info["is_supported"] is True
    assert info["file_type"] == "csv"
    assert info["loader_class"] == "CSVLoader"
