import pytest
import pandas as pd
from pydantic import BaseModel, Field
from unischema.validator import UniversalValidator, ValidationError, ValidationResult


class MockUserSchema(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2)
    email: str
    age: int | None = Field(None, ge=0, le=120)


@pytest.fixture
def validator():
    return UniversalValidator(MockUserSchema)


def test_validation_error_to_dict():
    err = ValidationError(
        row_index=5,
        column="age",
        error_type="less_than_equal",
        message="Input should be less than or equal to 120",
        value=150
    )
    assert err.to_dict() == {
        "row_index": 5,
        "column": "age",
        "error_type": "less_than_equal",
        "message": "Input should be less than or equal to 120",
        "value": "150"
    }
    assert "Row 5, Column 'age'" in str(err)


def test_validator_check_columns(validator):
    df_good = pd.DataFrame({"id": [1], "name": ["Alice"], "email": ["a@a.com"], "age": [20]})
    df_missing = pd.DataFrame({"name": ["Alice"], "email": ["a@a.com"]})
    
    check_good = validator.check_columns(df_good)
    assert check_good["compatible"] is True
    
    check_missing = validator.check_columns(df_missing)
    assert check_missing["compatible"] is False
    assert "id" in check_missing["missing_required"]


def test_validator_column_mapping():
    mapping = {"user_id": "id", "full_name": "name"}
    val = UniversalValidator(MockUserSchema, column_mapping=mapping)
    df = pd.DataFrame({
        "user_id": [1],
        "full_name": ["Alice"],
        "email": ["a@a.com"],
        "age": [20]
    })
    
    res = val.validate(df)
    assert res.valid_count == 1
    assert len(res.errors) == 0


def test_validator_validate_rows(validator):
    df = pd.DataFrame({
        "id": [1, -2, 3],  # row 1 invalid
        "name": ["Alice", "Bob", "C"],  # row 2 invalid
        "email": ["a@a.com", "b@b.com", "c@c.com"],
        "age": [20, None, 150]  # row 2 invalid
    })
    
    res = validator.validate(df)
    
    assert res.total_rows == 3
    assert res.valid_count == 1  # Alice
    assert res.invalid_count == 2
    
    assert res.success_rate == pytest.approx(33.33, abs=0.1)
    assert res.error_rate == pytest.approx(66.67, abs=0.1)
    
    errors = res.errors
    assert len(errors) == 3  # id, name, age
    
    # Check error grouping
    by_col = res.get_errors_by_column()
    assert "id" in by_col
    assert "name" in by_col
    assert "age" in by_col
    
    counts = res.get_error_counts_by_column()
    assert counts["id"] == 1
    
    summary = res.get_error_summary()
    assert summary["total_errors"] == 3
    
    # JSON serialization
    json_res = res.to_json()
    assert "MockUserSchema" in json_res


def test_validator_single(validator):
    valid_data = {"id": 1, "name": "Alice", "email": "a@a.com", "age": 20}
    invalid_data = {"id": -1, "name": "Alice", "email": "a@a.com"}
    
    is_valid, errors = validator.validate_single(valid_data)
    assert is_valid is True
    assert len(errors) == 0
    
    is_valid_inv, errors_inv = validator.validate_single(invalid_data)
    assert is_valid_inv is False
    assert len(errors_inv) == 1
    assert errors_inv[0].column == "id"


def test_validator_get_schema_info(validator):
    info = validator.get_schema_info()
    assert info["schema_name"] == "MockUserSchema"
    assert "id" in info["fields"]
    assert "id" in info["required_fields"]
    assert "age" in info["optional_fields"]
